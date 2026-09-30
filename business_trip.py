import argparse
import inspect
import os
from datetime import datetime
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PDF = BASE_DIR / "00_application-form.pdf"
ENV_FILE = BASE_DIR / ".env"
DEFAULT_OUTPUT = BASE_DIR / "business_trip_application_filled.pdf"

TEXT_FIELDS = {
    "service_unit": "Antragsteller.dienststelle",
    "applicant_name": "Antragsteller.Name",
    "department": "Antragsteller.Referat",
    "office_phone": "Antragsteller.telefondienstl",
    "home_address": "Antragsteller.adr1",
    "additional_home_address": "Antragsteller.adr2",
    "temporary_stay_address": "Antragsteller.adr3",
    "destination": "Antragsteller.reiseziel",
    "purpose": "Antragsteller.zweck",
    "overnight_cost_per_night": "uebernachtung1",
    "departure_date": "dat1",
    "departure_time": "uhr1",
    "business_start_date": "dat1a",
    "business_start_time": "uhr1a",
    "business_end_date": "dat1b",
    "business_end_time": "uhr1b",
    "return_date": "dat1c",
    "return_time": "uhr1c",
    "outbound_other_transport": "sonst1",
    "return_other_transport": "sonst2",
    "bahncard_number": "bcnr",
    "bahncard_valid_until": "gueltig",
    "travel_card_from": "streckevon",
    "travel_card_to": "streckenach",
    "bonus_program_name": "bonusprogramm",
    "private_car_reason": "begruendung1",
    "private_car_reason_continuation": "begruendung2",
    "flight_reason": "begruendung3",
    "flight_reason_continuation": "begruendung4",
    "private_stay_from": "dat2",
    "private_stay_until": "dat3",
    "private_stay_destination": "nach2",
    "iban": "ktonr",
    "bic": "blz",
    "bank_name": "bank",
    "explanations": "erlaeuterungen1",
    "explanations_continuation": "erlaeuterungen2",
    "application_date": "dat4",
}

DATE_FIELDS = {
    "departure_date",
    "business_start_date",
    "business_end_date",
    "return_date",
    "bahncard_valid_until",
    "private_stay_from",
    "private_stay_until",
    "application_date",
}

CHECKBOX_FIELDS = {
    "meals_provided_free": "kk4",
    "outbound_train": "kk7.1",
    "outbound_bus_or_public_transport": "kk7.2",
    "outbound_private_car": "kk7.3",
    "outbound_passenger_in_private_car": "kk7.4",
    "outbound_official_car": "kk7.5",
    "outbound_flight": "kk7.6",
    "outbound_other_transport_selected": "kk7.7",
    "return_train": "kk7.1a",
    "return_bus_or_public_transport": "kk7.2a",
    "return_private_car": "kk7.3a",
    "return_passenger_in_private_car": "kk7.4a",
    "return_official_car": "kk7.5a",
    "return_flight": "kk7.6a",
    "return_other_transport_selected": "kk7.7a",
    "uses_personal_travel_card": "kk7.20",
    "participates_in_bonus_program": "kk7.21",
    "requests_recognition_for_private_car": "kk8.1",
    "has_field_service_role": "kk8.2",
    "requests_flight_cost_reimbursement": "kk9.1",
    "uses_official_air_miles": "kk9.2",
    "requests_advance": "kk11",
}

RADIO_OPTIONS = {
    "application_kind": ("Beantragung", {"business-trip": 1, "training-trip": 2, "it-trip": 3}),
    "employment_status": (
        "beruf",
        {"civil-servant-or-judge": 1, "employee": 2, "temporary-civil-servant": 3, "trainee": 4},
    ),
    "additional_participants": ("wt", {"yes": 1, "no": 2}),
    "meal_provider": ("wegen", {"official": 1, "personal": 2}),
    "overnight_required": ("nacht", {"no": 1, "yes": 2}),
    "overnight_payment": ("unentgeltl", {"free": 1, "paid": 2}),
    "overnight_provider": ("wegen2", {"official": 1, "personal": 2}),
    "breakfast": ("Fruehstueck", {"with": 1, "without": 2}),
    "travel_start_from": (
        "beginn",
        {"home-a": 1, "home-b": 2, "office": 3, "temporary-address": 4},
    ),
    "travel_end_at": (
        "ende",
        {"home-a": 1, "home-b": 2, "office": 3, "temporary-address": 4},
    ),
    "bahncard_class": ("BC_2_1", {"second": 1, "first": 2}),
    "bahncard_rate": ("bcklasse", {"25": 1, "50": 2, "100": 3}),
}

ENV_DEFAULTS = {
    "service_unit": "SERVICE_UNIT",
    "applicant_name": "APPLICANT_NAME",
    "department": "DEPARTMENT",
    "office_phone": "OFFICE_PHONE",
    "home_address": "HOME_ADDRESS",
    "additional_home_address": "ADDITIONAL_HOME_ADDRESS",
    "temporary_stay_address": "TEMPORARY_STAY_ADDRESS",
    "iban": "IBAN",
    "bic": "BIC",
    "bank_name": "BANK_NAME",
}


def format_date(value: str) -> str:
    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, date_format).strftime("%d.%m.%Y")
        except ValueError:
            continue
    raise ValueError("Dates must use YYYY-MM-DD or DD.MM.YYYY format.")


def parse_datetime(date_value: str, time_value: str, label: str) -> datetime:
    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            parsed_date = datetime.strptime(date_value, date_format).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"{label} date must use YYYY-MM-DD or DD.MM.YYYY format.")

    try:
        parsed_time = datetime.strptime(time_value, "%H:%M").time()
    except ValueError as error:
        raise ValueError(f"{label} time must use HH:MM format.") from error
    return datetime.combine(parsed_date, parsed_time)


def create_business_trip_application(
    destination: str | None,
    purpose: str | None,
    departure_date: str | None,
    departure_time: str | None,
    business_start_date: str | None,
    business_start_time: str | None,
    business_end_date: str | None,
    business_end_time: str | None,
    return_date: str | None,
    return_time: str | None,
    service_unit: str | None = None,
    applicant_name: str | None = None,
    department: str | None = None,
    office_phone: str | None = None,
    home_address: str | None = None,
    additional_home_address: str | None = None,
    temporary_stay_address: str | None = None,
    overnight_cost_per_night: str | None = None,
    outbound_other_transport: str | None = None,
    return_other_transport: str | None = None,
    bahncard_number: str | None = None,
    bahncard_valid_until: str | None = None,
    travel_card_from: str | None = None,
    travel_card_to: str | None = None,
    bonus_program_name: str | None = None,
    private_car_reason: str | None = None,
    private_car_reason_continuation: str | None = None,
    flight_reason: str | None = None,
    flight_reason_continuation: str | None = None,
    private_stay_from: str | None = None,
    private_stay_until: str | None = None,
    private_stay_destination: str | None = None,
    iban: str | None = None,
    bic: str | None = None,
    bank_name: str | None = None,
    explanations: str | None = None,
    explanations_continuation: str | None = None,
    application_date: str | None = None,
    meals_provided_free: bool | None = None,
    outbound_train: bool | None = None,
    outbound_bus_or_public_transport: bool | None = None,
    outbound_private_car: bool | None = None,
    outbound_passenger_in_private_car: bool | None = None,
    outbound_official_car: bool | None = None,
    outbound_flight: bool | None = None,
    outbound_other_transport_selected: bool | None = None,
    return_train: bool | None = None,
    return_bus_or_public_transport: bool | None = None,
    return_private_car: bool | None = None,
    return_passenger_in_private_car: bool | None = None,
    return_official_car: bool | None = None,
    return_flight: bool | None = None,
    return_other_transport_selected: bool | None = None,
    uses_personal_travel_card: bool | None = None,
    participates_in_bonus_program: bool | None = None,
    requests_recognition_for_private_car: bool | None = None,
    has_field_service_role: bool | None = None,
    requests_flight_cost_reimbursement: bool | None = None,
    uses_official_air_miles: bool | None = None,
    requests_advance: bool | None = None,
    application_kind: str | None = None,
    employment_status: str | None = None,
    additional_participants: str | None = None,
    meal_provider: str | None = None,
    overnight_required: str | None = None,
    overnight_payment: str | None = None,
    overnight_provider: str | None = None,
    breakfast: str | None = None,
    travel_start_from: str | None = None,
    travel_end_at: str | None = None,
    bahncard_class: str | None = None,
    bahncard_rate: str | None = None,
) -> Path:
    """Fill applicant-editable fields in the business-trip application PDF."""
    return create_business_trip_application_int(**locals())

def create_business_trip_application_int(output_path:str = DEFAULT_OUTPUT, template_path: str | Path = TEMPLATE_PDF, 
                                         service_unit: str | None = None,
                                             applicant_name: str | None = None,
                                             department: str | None = None,
                                             office_phone: str | None = None,
                                             home_address: str | None = None,
                                             additional_home_address: str | None = None,
                                             temporary_stay_address: str | None = None,
                                             destination: str | None = None,
                                             purpose: str | None = None,
                                             overnight_cost_per_night: str | None = None,
                                             departure_date: str | None = None,
                                             departure_time: str | None = None,
                                             business_start_date: str | None = None,
                                             business_start_time: str | None = None,
                                             business_end_date: str | None = None,
                                             business_end_time: str | None = None,
                                             return_date: str | None = None,
                                             return_time: str | None = None,
                                             outbound_other_transport: str | None = None,
                                             return_other_transport: str | None = None,
                                             bahncard_number: str | None = None,
                                             bahncard_valid_until: str | None = None,
                                             travel_card_from: str | None = None,
                                             travel_card_to: str | None = None,
                                             bonus_program_name: str | None = None,
                                             private_car_reason: str | None = None,
                                             private_car_reason_continuation: str | None = None,
                                             flight_reason: str | None = None,
                                             flight_reason_continuation: str | None = None,
                                             private_stay_from: str | None = None,
                                             private_stay_until: str | None = None,
                                             private_stay_destination: str | None = None,
                                             iban: str | None = None,
                                             bic: str | None = None,
                                             bank_name: str | None = None,
                                             explanations: str | None = None,
                                             explanations_continuation: str | None = None,
                                             application_date: str | None = None,
                                             meals_provided_free: bool | None = None,
                                             outbound_train: bool | None = None,
                                             outbound_bus_or_public_transport: bool | None = None,
                                             outbound_private_car: bool | None = None,
                                             outbound_passenger_in_private_car: bool | None = None,
                                             outbound_official_car: bool | None = None,
                                             outbound_flight: bool | None = None,
                                             outbound_other_transport_selected: bool | None = None,
                                             return_train: bool | None = None,
                                             return_bus_or_public_transport: bool | None = None,
                                             return_private_car: bool | None = None,
                                             return_passenger_in_private_car: bool | None = None,
                                             return_official_car: bool | None = None,
                                             return_flight: bool | None = None,
                                             return_other_transport_selected: bool | None = None,
                                             uses_personal_travel_card: bool | None = None,
                                             participates_in_bonus_program: bool | None = None,
                                             requests_recognition_for_private_car: bool | None = None,
                                             has_field_service_role: bool | None = None,
                                             requests_flight_cost_reimbursement: bool | None = None,
                                             uses_official_air_miles: bool | None = None,
                                             requests_advance: bool | None = None,
                                             application_kind: str | None = None,
                                             employment_status: str | None = None,
                                             additional_participants: str | None = None,
                                             meal_provider: str | None = None,
                                             overnight_required: str | None = None,
                                             overnight_payment: str | None = None,
                                             overnight_provider: str | None = None,
                                             breakfast: str | None = None,
                                             travel_start_from: str | None = None,
                                             travel_end_at: str | None = None,
                                             bahncard_class: str | None = None,
                                             bahncard_rate: str | None = None
                                         ):
    load_dotenv(ENV_FILE)

    values = locals().copy()
    values.pop("output_path")
    values.pop("template_path")
    for argument, variable in ENV_DEFAULTS.items():
        if values[argument] is None:
            values[argument] = os.getenv(variable)

    trip_times = (
        ("departure_date", "departure_time", "business_start_date", "business_start_time"),
        ("business_end_date", "business_end_time", "return_date", "return_time"),
    )
    for earlier_date, earlier_time, later_date, later_time in trip_times:
        if all(values[name] is not None for name in (earlier_date, earlier_time, later_date, later_time)):
            earlier = parse_datetime(values[earlier_date], values[earlier_time], earlier_date.replace("_", " ").capitalize())
            later = parse_datetime(values[later_date], values[later_time], later_date.replace("_", " ").capitalize())
            if earlier >= later:
                if earlier_date == "departure_date":
                    raise ValueError("Departure date/time must be before business start date/time.")
                raise ValueError("Return date/time must be after business end date/time.")

    source = Path(template_path).expanduser().resolve()
    destination = Path(output_path).expanduser().resolve()
    if source == destination:
        raise ValueError("The output PDF must not overwrite the template.")

    reader = PdfReader(source)
    field_definitions = reader.get_fields() or {}
    form_values: dict[str, str | NameObject] = {}

    for argument, pdf_field in TEXT_FIELDS.items():
        value = values[argument]
        if value is not None:
            form_values[pdf_field] = format_date(value) if argument in DATE_FIELDS else value

    for argument, pdf_field in CHECKBOX_FIELDS.items():
        selected = values[argument]
        if selected is None:
            continue
        states = [state for state in field_definitions[pdf_field]["/_States_"] if state != "/Off"]
        if len(states) != 1:
            raise ValueError(f"Expected a single checkbox state for {pdf_field}.")
        form_values[pdf_field] = NameObject(states[0] if selected else "/Off")

    for argument, (pdf_field, choices) in RADIO_OPTIONS.items():
        selected = values[argument]
        if selected is None:
            continue
        states = [state for state in field_definitions[pdf_field]["/_States_"] if state != "/Off"]
        form_values[pdf_field] = NameObject(states[choices[selected] - 1])

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fill the applicant section of the business-trip PDF.")
    parser.add_argument("--template", type=Path, default=TEMPLATE_PDF, help="Path to the blank PDF form.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path for the filled PDF.")

    for name, parameter in inspect.signature(create_business_trip_application).parameters.items():
        if name in {"output_path", "template_path"}:
            continue
        option = "--" + name.replace("_", "-")
        if name in CHECKBOX_FIELDS:
            parser.add_argument(option, action=argparse.BooleanOptionalAction, default=None)
        elif name in RADIO_OPTIONS:
            parser.add_argument(option, choices=tuple(RADIO_OPTIONS[name][1]), default=None)
        else:
            default = os.getenv(ENV_DEFAULTS[name]) if name in ENV_DEFAULTS else None
            parser.add_argument(option, default=default)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv(ENV_FILE)
    parser = build_parser()
    arguments = vars(parser.parse_args(argv))
    output_path = arguments.pop("output")
    template_path = arguments.pop("template")
    result = create_business_trip_application_int(
        output_path=output_path,
        template_path=template_path,
        **arguments,
    )
    print(f"Filled application written to {result}")
    os.startfile(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())