"""Form-independent helpers for filling the applicant fields of a PDF form."""

import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_OUTPUT_NAME = "business_trip_application_filled.pdf"

INPUT_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")

# (earlier, later, may be equal, error message) for the four moments of a trip
TRIP_ORDER = (
    ("departure", "business_start", False, "Departure date/time must be before business start date/time."),
    ("business_start", "business_end", True, "Business start date/time must not be after business end date/time."),
    ("business_end", "return", False, "Return date/time must be after business end date/time."),
)


def load_env() -> None:
    load_dotenv(ENV_FILE)


def with_env_defaults(values: dict, env_defaults: dict[str, str]) -> dict:
    """Return a copy of `values` in which unset arguments fall back to variables from .env."""
    load_env()
    values = dict(values)
    for argument, variable in env_defaults.items():
        if values.get(argument) is None:
            values[argument] = os.getenv(variable) or None
    return values


def parse_date(value: str, label: str = "Dates") -> date:
    for date_format in INPUT_DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"{label} must use YYYY-MM-DD or DD.MM.YYYY format.")


def format_date(value: str, output_format: str = "%d.%m.%Y") -> str:
    return parse_date(value).strftime(output_format)


def parse_datetime(date_value: str, time_value: str, label: str) -> datetime:
    parsed_date = parse_date(date_value, f"{label} date")
    try:
        parsed_time = datetime.strptime(time_value, "%H:%M").time()
    except ValueError as error:
        raise ValueError(f"{label} time must use HH:MM format.") from error
    return datetime.combine(parsed_date, parsed_time)


def check_trip_times(values: dict) -> None:
    """Check that departure, business start, business end and return are in chronological order."""
    for earlier, later, may_be_equal, message in TRIP_ORDER:
        names = [f"{moment}_{part}" for moment in (earlier, later) for part in ("date", "time")]
        if any(values.get(name) is None for name in names):
            continue
        start = parse_datetime(values[f"{earlier}_date"], values[f"{earlier}_time"], earlier.replace("_", " ").capitalize())
        end = parse_datetime(values[f"{later}_date"], values[f"{later}_time"], later.replace("_", " ").capitalize())
        if start > end or (start == end and not may_be_equal):
            raise ValueError(message)


def map_fields(
    values: dict,
    text_fields: dict[str, str],
    date_formats: dict[str, str],
    checkbox_fields: dict[str, str],
    choices: dict[str, tuple[str, dict[str, str]]],
) -> tuple[dict[str, str], dict[str, bool | str]]:
    """Translate function arguments into PDF field values.

    Returns the text field values and the button values: True/False for checkboxes and
    the readable label of the selected option for choice fields.
    """
    text: dict[str, str] = {}
    for argument, pdf_field in text_fields.items():
        value = values.get(argument)
        if value is not None:
            text[pdf_field] = format_date(value, date_formats[argument]) if argument in date_formats else value

    buttons: dict[str, bool | str] = {}
    for argument, pdf_field in checkbox_fields.items():
        if values.get(argument) is not None:
            buttons[pdf_field] = bool(values[argument])
    for argument, (pdf_field, labels) in choices.items():
        selected = values.get(argument)
        if selected is None:
            continue
        if selected not in labels:
            raise ValueError(f"{argument} must be one of: {', '.join(labels)}.")
        buttons[pdf_field] = labels[selected]
    return text, buttons


def readable(state: str) -> str:
    """Return the text of a PDF name such as an export value.

    pypdf decodes names that are not UTF-8 with a GBK fallback, so Latin-1 umlauts come out as
    CJK characters ("persönlich" becomes "pers鰊lich"). This undoes that for display and lookup.
    """
    text = state[1:]
    if any(char >= "⺀" for char in text):
        try:
            text = text.encode("gbk").decode("cp1252")
        except UnicodeError:
            pass
    return text.strip()


def ancestors(node: DictionaryObject):
    """Yield a field node and its parents, nearest first."""
    while node is not None:
        yield node
        node = node["/Parent"].get_object() if "/Parent" in node else None


def qualified_name(field: DictionaryObject) -> str:
    return ".".join(reversed([node["/T"] for node in ancestors(field) if "/T" in node]))


def field_type(field: DictionaryObject) -> str | None:
    return next((node["/FT"] for node in ancestors(field) if "/FT" in node), None)


def button_states(reader: PdfReader) -> dict[str, dict[str, NameObject]]:
    """Map each checkbox or radio field to {readable label: raw on-state}, read from its widgets.

    Checkbox groups (several widgets sharing one field) have no /_States_ in pypdf's
    get_fields(), so the on-states are taken from the widgets' appearance streams instead.
    """
    states: dict[str, dict[str, NameObject]] = {}
    for page in reader.pages:
        for annotation in page.get("/Annots") or []:
            widget = annotation.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            field = widget if "/T" in widget else widget["/Parent"].get_object()
            if field_type(field) != "/Btn" or "/AP" not in widget or "/N" not in widget["/AP"]:
                continue
            appearances = widget["/AP"]["/N"]
            if not isinstance(appearances, DictionaryObject):
                continue
            options = states.setdefault(qualified_name(field), {})
            for state in appearances:
                if state != "/Off":
                    options[readable(state)] = state
    return states


def default_output_path() -> Path:
    load_env()
    output_dir = Path(os.getenv("OUTPUT_DIR") or DEFAULT_OUTPUT_DIR).expanduser()
    if not output_dir.is_absolute():
        output_dir = BASE_DIR / output_dir
    return output_dir / DEFAULT_OUTPUT_NAME


def fill_pdf(
    template_path: str | Path,
    text_values: dict[str, str],
    button_values: dict[str, bool | str],
    output_path: str | Path | None = None,
) -> Path:
    """Write a copy of the template with the given field values; never overwrites an existing file."""
    source = Path(template_path).expanduser().resolve()
    destination = Path(output_path or default_output_path()).expanduser().resolve()
    if source == destination:
        raise ValueError("The output PDF must not overwrite the template.")

    reader = PdfReader(source)
    states = button_states(reader)
    form_values: dict[str, str | NameObject] = dict(text_values)
    for pdf_field, selected in button_values.items():
        options = states.get(pdf_field)
        if not options:
            raise ValueError(f"The form has no checkbox or radio field {pdf_field!r}.")
        if isinstance(selected, bool):
            if len(options) != 1:
                raise ValueError(f"Expected a single checkbox state for {pdf_field}.")
            form_values[pdf_field] = next(iter(options.values())) if selected else NameObject("/Off")
        elif selected in options:
            form_values[pdf_field] = options[selected]
        else:
            raise ValueError(f"Field {pdf_field!r} has no option {selected!r}; options: {', '.join(options)}.")

    writer = PdfWriter(clone_from=source)
    for page in writer.pages:
        writer.update_page_form_field_values(page, form_values, auto_regenerate=False)

    destination.parent.mkdir(parents=True, exist_ok=True)
    requested_destination = destination
    suffix = 0
    while True:
        try:
            with destination.open("xb") as output_file:
                writer.write(output_file)
            break
        except FileExistsError:
            suffix += 1
            destination = requested_destination.with_name(
                f"{requested_destination.stem}-{suffix}{requested_destination.suffix}"
            )
    return destination
