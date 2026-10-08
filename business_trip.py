"""Command line interface for filling business-trip application PDFs.

The forms live in their own modules (form_saxony.py, ...). `create_business_trip_application`
is still importable from here and fills the Saxon form, as it did before other forms existed.
"""

import argparse
import inspect
import os
from pathlib import Path
from typing import Literal, Sequence, get_args, get_origin

import form_saxony
import pdf_form
from form_saxony import (  # re-exported for existing imports
    CHECKBOX_FIELDS,
    CHOICES,
    ENV_DEFAULTS,
    TEMPLATE_PDF,
    TEXT_FIELDS,
    create_business_trip_application,
)
from pdf_form import format_date, parse_datetime  # re-exported for existing imports


FORMS = {form_saxony.NAME: form_saxony}
DEFAULT_FORM = form_saxony.NAME


def get_form(name: str | None = None):
    """Return the form module by name; without a name, the one set as DRA_FORM in .env."""
    pdf_form.load_env()
    name = name or os.getenv("DRA_FORM") or DEFAULT_FORM
    if name not in FORMS:
        raise ValueError(f"Unknown form {name!r}; choose one of: {', '.join(FORMS)}.")
    return FORMS[name]


def create_business_trip_application_int(
    output_path: str | Path | None = None, template_path: str | Path = TEMPLATE_PDF, **values
) -> Path:
    """Fill the Saxon form with an explicit output path (kept for existing callers)."""
    return form_saxony.fill(values, output_path, template_path)


def literal_choices(annotation) -> tuple[str, ...] | None:
    """Return the allowed values of a `Literal[...] | None` annotation."""
    for option in get_args(annotation) or (annotation,):
        if get_origin(option) is Literal:
            return get_args(option)
    return None


def build_parser(form=form_saxony) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Fill the applicant section of the business-trip PDF ({form.TITLE})."
    )
    parser.add_argument(
        "--form",
        choices=tuple(FORMS),
        default=form.NAME,
        help="Form to fill; the options below belong to the selected form (default: DRA_FORM from .env, else saxony).",
    )
    parser.add_argument("--template", type=Path, default=form.TEMPLATE_PDF, help="Path to the blank PDF form.")
    parser.add_argument(
        "--output", type=Path, default=None, help="Path for the filled PDF (default: OUTPUT_DIR from .env, else output/)."
    )

    for name, parameter in inspect.signature(form.create_business_trip_application).parameters.items():
        option = "--" + name.replace("_", "-")
        choices = literal_choices(parameter.annotation)
        if bool in get_args(parameter.annotation):
            parser.add_argument(option, action=argparse.BooleanOptionalAction, default=None)
        elif choices:
            parser.add_argument(option, choices=choices, default=None)
        else:
            parser.add_argument(option, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    form_option = argparse.ArgumentParser(add_help=False)
    form_option.add_argument("--form", choices=tuple(FORMS), default=None)
    form = get_form(form_option.parse_known_args(argv)[0].form)

    arguments = vars(build_parser(form).parse_args(argv))
    arguments.pop("form")
    output_path = arguments.pop("output")
    template_path = arguments.pop("template")
    result = form.fill(arguments, output_path, template_path)
    print(f"Filled application written to {result}")
    os.startfile(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
