"""TU Dresden business-trip application form: Beantragung einer Dienstreise (RK-02)."""

import inspect
from pathlib import Path
from typing import Literal

from pdf_form import (
    BASE_DIR,
    check_known_arguments,
    fill_pdf,
    format_date,
    map_fields,
    validate_trip_times,
    with_env_defaults,
)


NAME = "tud"
TITLE = "TU Dresden RK-02, Beantragung einer Dienstreise"
TEMPLATE_PDF = BASE_DIR / "00_application-form-dresden.pdf"

# Reisezweck is a single line; longer text is cut off in the PDF.
PURPOSE_MAX_LENGTH = 70

TEXT_FIELDS = {
    "service_unit": "Struktureinheit",
    "applicant_name": "Reisender Name Vorname",
    "personnel_number": "PersonalNr TUD",
    "department": "InstDez SGRow1",
    "office_phone": "Telefon dienstlRow1",
    "home_address": "Adresse der Wohnung",
    "additional_home_address": "Adresse weitere Wohnung",
    "temporary_stay_address": "Adresse vorübergehender Aufenthaltsort",
    "destination": "Reiseziele",
    "purpose": "Reisezweck",
    "overnight_cost_per_night": "Kosten in EUR/Nacht",
    "bahncard_number": "BCNr",
    "bahncard_valid_until": "BahnCard gültigkeit",
    "travel_card_from": "Strecke von",
    "travel_card_to": "Strecke nach",
    "bonus_program_name": "Bezeichnung Bonusprogramm",
    "private_car_reason": "Begründung privates KFZ / Mietwagen",
    "flight_reason": "Begründung",
    "private_stay_from": "Datum privatreise_af_date",
    "private_stay_until": "Datum6_af_date",
    "private_stay_destination": "Nach",
    "iban": "IBAN",
    "bic": "BIC",
    "bank_name": "Geldinstitut",
    "explanations": "Weitere Erläuterungen z B Angaben über Kostenerstattung durch Dritte",
    "application_date": "Datum Antrag_af_date",
}

# The form's own date scripts (AFDate_FormatEx) expect two-digit years in the narrow date cells.
DATE_FORMATS = {
    "bahncard_valid_until": "%d.%m.%Y",
    "private_stay_from": "%d.%m.%y",
    "private_stay_until": "%d.%m.%y",
    "application_date": "%d.%m.%Y",
}
SCHEDULE_DATE_FORMAT = "%d.%m.%y"

CHECKBOX_FIELDS = {
    "meals_provided_free": "verpflegung",
    "outbound_train": "Bahn Hinfahrt",
    "outbound_bus_or_public_transport": "Bus / ÖPNV Hinfahrt",
    "outbound_private_car": "privates KFZ → ggf. Nr. 8 Hinfahrt",
    "outbound_rental_car": "Mietwagen → Nr. 8 Hinfahrt",
    "outbound_passenger_in_private_car": "Mitfahrt im privaten KFZ/ Mietwagen / Dienst-KFZ Hinfahrt",
    "outbound_official_car": "Dienst-KFZ Hinfahrt",
    "outbound_flight": "Flugzeug → Nr. 9 Hinfahrt",
    "outbound_other_transport_selected": "Sonstiges (z.B. Taxi, Fahrrad) Hinfahrt",
    "return_train": "Bahn Rückfahrt",
    "return_bus_or_public_transport": "Bus / ÖPNV Rückfahrt",
    "return_private_car": "privates KFZ → ggf. Nr. 8 Rückfahrt",
    "return_rental_car": "Mietwagen → Nr. 8 Rückfahrt",
    "return_passenger_in_private_car": "Mitfahrt im privaten KFZ/ Mietwagen / Dienst-KFZ Rückfahrt",
    "return_official_car": "Dienst-KFZ Rückfahrt",
    "return_flight": "Flugzeug → Nr. 9  Rückfahrt",
    "return_other_transport_selected": "Sonstiges (z.B. Taxi, Fahrrad)  Rückfahrt",
    "uses_personal_travel_card": "Persönliche Zeitkarte",
    "participates_in_bonus_program": "Bonusprogramm",
    "requests_recognition_for_private_car": "Triftige Gründe privates KFZ",
    "requests_flight_cost_reimbursement": "Erstattung Flugkosten",
    "uses_official_air_miles": "Meilengutschriften",
    "requests_advance": "Abschlagsbeantragung",
}

# argument -> (PDF field, {argument value: option label as printed in the PDF})
CHOICES = {
    "application_kind": (
        "Reiseart",
        {
            "business-trip": "Dienstreise",
            "third-party-interest-trip": 'Reise im dienstlichen Interesse der TUD ("Dritte")',
            "training-trip": "Aus-/Fortbildungsreise (hier nur teilweise Kostenbeteiligung des Dienstherrn, "
            "da nur teilweise in dienstlichen Interesse)",
        },
    ),
    "employment_status": (
        "Tätigkeitsart",
        {
            "civil-servant-or-judge": "Beamter / Beamtin",
            "senior-professor": "Seniorprofessor/in",
            "employee": "Arbeitnehmer/in",
            "trainee": "Auszubildende/r",
            "student-assistant": "SHK/WHK",
            "student": "Student/in",
            "external-person": "externe Person",
        },
    ),
    "additional_participants": ("Weitere Teilnehmer", {"yes": "ja", "no": "nein"}),
    "meal_provider": (
        "unentgeltliche Verpflegung Grund",
        {"official": "des Amtes wegen", "personal": "aus persönlichen Gründen"},
    ),
    "overnight_required": ("Übernachtung", {"no": "nein", "yes": "ja"}),
    "overnight_payment": ("Kosten Übernachtung", {"free": "unentgeltlich", "paid": "nicht unentgeltlich"}),
    "overnight_provider": (
        "unentgeltliche Übernachtung Grund",
        {"official": "des Amtes wegen", "personal": "aus persönlichen Gründen"},
    ),
    "breakfast": (
        "Kosten Frühstück",
        {"with": "inklusive Kosten des Frühstückes", "without": "ohne Kosten des Frühstücks"},
    ),
    "bahncard_type": ("BahnCard", {"bahncard": "BahnCard", "business": "BahnCard Business"}),
    "bahncard_class": ("BahnCard Klasse", {"second": "2. Klasse", "first": "1. Klasse"}),
    "bahncard_rate": ("BahnCard Art", {"25": "25", "50": "50", "100": "100"}),
}

# Section 6 is a grid: one row per place where the trip starts or ends. Departure, business start
# and business end go into the start row, the return into the end row. Some field names are
# irregular, e.g. the end-of-trip date of the office row is called "...Ende Dienstgeschäft an...".
SCHEDULE_ROWS = {
    "home-a": {
        "start_box": "Check Box - Reiseverlauf",
        "departure_date": "Datum Beginn Reise Wohnung A_af_date",
        "departure_time": "Beginn der Reise Uhr Wohnung A",
        "business_start_date": "Datum Beginn Dienstgeschäft Wohnung A",
        "business_start_time": "Beginn Dienstgeschäft Uhr Wohnung A",
        "business_end_date": "Datum Ende Dienstgeschäft Wohnung A",
        "business_end_time": "Ende Dienstgeschäft Uhr Wohnung A",
        "end_box": "Check Box - Reiseverlauf5",
        "return_date": "Datum Ende Reise Wohnung A",
        "return_time": "Ende der Reise Uhr Wohnung A",
    },
    "home-b": {
        "start_box": "Check Box Reiseverlauf2",
        "departure_date": "Datum Beginn Reise Wohnung B",
        "departure_time": "Beginn der Reise Uhr Wohnung B",
        "business_start_date": "Datum Beginn Dienstgeschäft Wohnung B",
        "business_start_time": "Beginn Dienstgeschäft Uhr Wohnung B",
        "business_end_date": "Datum Ende Dienstgeschäft Wohnung B",
        "business_end_time": "Ende Dienstgeschäft Uhr Wohnung B",
        "end_box": "Check Box Reiseverlauf6",
        "return_date": "Datum Ende Reise Wohnung B",
        "return_time": "Ende der Reise Uhr Wohnung B",
    },
    "office": {
        "start_box": "Check Box Reiseverlauf3",
        "departure_date": "Datum Beginn Reise Dienststelle_af_date",
        "departure_time": "Beginn der Reise Uhr Dienststelle",
        "business_start_date": "Datum Beginn Dienstgeschäft Dienststelle",
        "business_start_time": "Beginn Dienstgeschäft Uhr Dienststelle",
        "business_end_date": "Datum Ende Dienstgeschäft Dienststelle",
        "business_end_time": "Ende Dienstgeschäft Uhr Dienststelle",
        "end_box": "Check Box Reiseverlauf7",
        "return_date": "Datum Ende Dienstgeschäft an Dienststelle",
        "return_time": "Ende der Reise Uhr Dienststelle",
    },
    "temporary-address": {
        "start_box": "Check Box Reiseverlauf4",
        "departure_date": "Datum Beginn Reise vorübergehender Aufenthaltsort",
        "departure_time": "Beginn der Reise Uhr vorübergehender Aufenthaltsort",
        "business_start_date": "Datum Beginn Dienstgeschäft vorübergehender Aufenthaltsort",
        "business_start_time": "Beginn Dienstgeschäft Uhr vorübergehender Aufenthaltsort",
        "business_end_date": "Datum Ende Dienstgeschäft vorübergehender Aufenthaltsort",
        "business_end_time": "Ende Dienstgeschäft Uhr vorübergehender Aufenthaltsort",
        "end_box": "Check Box Reiseverlauf8",
        "return_date": "Datum Ende Reise vorübergehender Aufenthaltsort",
        "return_time": "Ende der Reise Uhr vorübergehender Aufenthaltsort",
    },
}

# (row argument, row checkbox, trip moments entered in that row)
SCHEDULE_PARTS = (
    ("travel_start_from", "start_box", ("departure", "business_start", "business_end")),
    ("travel_end_at", "end_box", ("return",)),
)

ENV_DEFAULTS = {
    "service_unit": "SERVICE_UNIT",
    "applicant_name": "APPLICANT_NAME",
    "personnel_number": "PERSONNEL_NUMBER",
    "department": "DEPARTMENT",
    "office_phone": "OFFICE_PHONE",
    "home_address": "HOME_ADDRESS",
    "additional_home_address": "ADDITIONAL_HOME_ADDRESS",
    "temporary_stay_address": "TEMPORARY_STAY_ADDRESS",
    "iban": "IBAN",
    "bic": "BIC",
    "bank_name": "BANK_NAME",
    "travel_start_from": "TRAVEL_START_FROM",
    "travel_end_at": "TRAVEL_END_AT",
}

GUIDE_NOTES = f"""
## Notes for this form (TU Dresden RK-02)
- `purpose` is a single line of at most {PURPOSE_MAX_LENGTH} characters. Put further detail
  (programme, invitation, who pays what) into `explanations`.
- The schedule (section 6) has one row per place where the trip starts or ends:
  `travel_start_from` and `travel_end_at` are `home-a` (main home), `home-b` (second
  home), `office` or `temporary-address`. They may be configured in .env; if the tool
  reports that one is missing, ask the user where the trip starts and ends.
- `application_kind`: `business-trip` (Dienstreise), `training-trip`
  (Aus-/Fortbildungsreise) or `third-party-interest-trip` (trip in the interest of
  TU Dresden by an external person).
- Rental cars: `outbound_rental_car` / `return_rental_car`, with the reason in
  `private_car_reason`. Passengers in any car use `*_passenger_in_private_car`.
- `personnel_number` (Personal-Nr. TUD) is personal data from .env; never invent it.
- Mention to the user when relevant: trips to other EU countries need an A1
  certificate (A1-Bescheinigung); section 18 (advance payment, bank details) must be
  complete before signing electronically; the form is either fully digital with
  qualified electronic signatures or printed and signed by hand, not a mix.
"""

Place = Literal["home-a", "home-b", "office", "temporary-address"]


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
    travel_start_from: Place | None = None,
    travel_end_at: Place | None = None,
    service_unit: str | None = None,
    applicant_name: str | None = None,
    personnel_number: str | None = None,
    department: str | None = None,
    office_phone: str | None = None,
    home_address: str | None = None,
    additional_home_address: str | None = None,
    temporary_stay_address: str | None = None,
    overnight_cost_per_night: str | None = None,
    bahncard_number: str | None = None,
    bahncard_valid_until: str | None = None,
    travel_card_from: str | None = None,
    travel_card_to: str | None = None,
    bonus_program_name: str | None = None,
    private_car_reason: str | None = None,
    flight_reason: str | None = None,
    private_stay_from: str | None = None,
    private_stay_until: str | None = None,
    private_stay_destination: str | None = None,
    iban: str | None = None,
    bic: str | None = None,
    bank_name: str | None = None,
    explanations: str | None = None,
    application_date: str | None = None,
    meals_provided_free: bool | None = None,
    outbound_train: bool | None = None,
    outbound_bus_or_public_transport: bool | None = None,
    outbound_private_car: bool | None = None,
    outbound_rental_car: bool | None = None,
    outbound_passenger_in_private_car: bool | None = None,
    outbound_official_car: bool | None = None,
    outbound_flight: bool | None = None,
    outbound_other_transport_selected: bool | None = None,
    return_train: bool | None = None,
    return_bus_or_public_transport: bool | None = None,
    return_private_car: bool | None = None,
    return_rental_car: bool | None = None,
    return_passenger_in_private_car: bool | None = None,
    return_official_car: bool | None = None,
    return_flight: bool | None = None,
    return_other_transport_selected: bool | None = None,
    uses_personal_travel_card: bool | None = None,
    participates_in_bonus_program: bool | None = None,
    requests_recognition_for_private_car: bool | None = None,
    requests_flight_cost_reimbursement: bool | None = None,
    uses_official_air_miles: bool | None = None,
    requests_advance: bool | None = None,
    application_kind: Literal["business-trip", "third-party-interest-trip", "training-trip"] | None = None,
    employment_status: Literal[
        "civil-servant-or-judge",
        "senior-professor",
        "employee",
        "trainee",
        "student-assistant",
        "student",
        "external-person",
    ]
    | None = None,
    additional_participants: Literal["yes", "no"] | None = None,
    meal_provider: Literal["official", "personal"] | None = None,
    overnight_required: Literal["no", "yes"] | None = None,
    overnight_payment: Literal["free", "paid"] | None = None,
    overnight_provider: Literal["official", "personal"] | None = None,
    breakfast: Literal["with", "without"] | None = None,
    bahncard_type: Literal["bahncard", "business"] | None = None,
    bahncard_class: Literal["second", "first"] | None = None,
    bahncard_rate: Literal["25", "50", "100"] | None = None,
) -> Path:
    """Fill applicant-editable fields in the TU Dresden business-trip application PDF (RK-02).

    Args:
        purpose: At most 70 characters (one line on the form); put details into explanations.
        departure_date: YYYY-MM-DD or DD.MM.YYYY, like all dates.
        departure_time: HH:MM (24h), like all times.
        travel_start_from: Schedule row where the trip starts; business start and end are entered in it too.
        travel_end_at: Schedule row where the trip ends, usually the same as travel_start_from.
        personnel_number: Personal-Nr. TU Dresden, from .env; never invent it.
        outbound_passenger_in_private_car: Passenger in a private, rental or official car.
        return_passenger_in_private_car: Passenger in a private, rental or official car.
        employment_status: student-assistant means SHK/WHK.
    """
    return fill(locals())


PARAMETERS = frozenset(inspect.signature(create_business_trip_application).parameters)


def schedule_fields(values: dict) -> tuple[dict[str, str], dict[str, bool]]:
    """Place departure, business start/end and return in the rows of the schedule grid."""
    text: dict[str, str] = {}
    buttons: dict[str, bool] = {}
    for row_argument, row_box, moments in SCHEDULE_PARTS:
        given = [
            f"{moment}_{part}"
            for moment in moments
            for part in ("date", "time")
            if values.get(f"{moment}_{part}") is not None
        ]
        row = values.get(row_argument)
        if row is None:
            if given:
                raise ValueError(
                    f"{row_argument} is needed to place {', '.join(given)} in the schedule (section 6). "
                    f"Ask the user where the trip {'starts' if row_box == 'start_box' else 'ends'}: "
                    f"{', '.join(SCHEDULE_ROWS)} (home-a is the main home), "
                    f"or set {ENV_DEFAULTS[row_argument]} in .env."
                )
            continue
        if row not in SCHEDULE_ROWS:
            raise ValueError(f"{row_argument} must be one of: {', '.join(SCHEDULE_ROWS)}.")

        cells = SCHEDULE_ROWS[row]
        buttons[cells[row_box]] = True
        for name in given:
            value = values[name]
            text[cells[name]] = format_date(value, SCHEDULE_DATE_FORMAT) if name.endswith("_date") else value
    return text, buttons


def fill(values: dict, output_path: str | Path | None = None, template_path: str | Path = TEMPLATE_PDF) -> Path:
    """Fill the form from a dict of `create_business_trip_application` arguments."""
    check_known_arguments(values, PARAMETERS, NAME)
    values = with_env_defaults(values, ENV_DEFAULTS)
    values = validate_trip_times(values)
    purpose = values.get("purpose")
    if purpose is not None and len(purpose) > PURPOSE_MAX_LENGTH:
        raise ValueError(
            f"purpose has {len(purpose)} characters but the form only has room for {PURPOSE_MAX_LENGTH}; "
            "shorten it and put the details into explanations."
        )
    text, buttons = map_fields(values, TEXT_FIELDS, DATE_FORMATS, CHECKBOX_FIELDS, CHOICES)
    schedule_text, schedule_buttons = schedule_fields(values)
    return fill_pdf(template_path, text | schedule_text, buttons | schedule_buttons, output_path)
