"""Saxon business-trip application form: Dienstreiseantrag Anlage 1 zur VwV-SächsRKG."""

import inspect
from pathlib import Path
from typing import Literal

from pdf_form import BASE_DIR, check_trip_times, fill_pdf, map_fields, with_env_defaults


NAME = "saxony"
TITLE = "Dienstreiseantrag Anlage 1 (VwV-SächsRKG)"
TEMPLATE_PDF = BASE_DIR / "00_application-form.pdf"

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

DATE_FORMATS = dict.fromkeys(
    (
        "departure_date",
        "business_start_date",
        "business_end_date",
        "return_date",
        "bahncard_valid_until",
        "private_stay_from",
        "private_stay_until",
        "application_date",
    ),
    "%d.%m.%Y",
)

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

TRAVEL_PLACES = {
    "home-a": "Wohnung a",
    "home-b": "Wohnung b",
    "office": "Dienststelle",
    "temporary-address": "voruebergehender Aufenthaltsort",
}

# argument -> (PDF field, {argument value: option label as printed in the PDF})
CHOICES = {
    "application_kind": (
        "Beantragung",
        {"business-trip": "Dienstreise", "training-trip": "Aus-/Fortbildungsreise", "it-trip": "IT-Reise"},
    ),
    "employment_status": (
        "beruf",
        {
            "civil-servant-or-judge": "Beamter/Richter",
            "employee": "Arbeitnehmer",
            "temporary-civil-servant": "Beamter a.W.",
            "trainee": "Auszubildender",
        },
    ),
    "additional_participants": ("wt", {"yes": "ja", "no": "nein"}),
    "meal_provider": ("wegen", {"official": "des Amtes wegen", "personal": "aus persönlichen Gründen"}),
    "overnight_required": ("nacht", {"no": "nein", "yes": "ja"}),
    "overnight_payment": ("unentgeltl", {"free": "unentgeltlich", "paid": "nicht unentgeltlich"}),
    "overnight_provider": ("wegen2", {"official": "des Amtes wegen", "personal": "aus persönlichen Gründen"}),
    "breakfast": ("Fruehstueck", {"with": "mit", "without": "ohne"}),
    "travel_start_from": ("beginn", TRAVEL_PLACES),
    "travel_end_at": ("ende", TRAVEL_PLACES),
    "bahncard_class": ("BC_2_1", {"second": "2. Klasse", "first": "1. Klasse"}),
    "bahncard_rate": ("bcklasse", {"25": "25", "50": "50", "100": "100"}),
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
    "travel_start_from": "TRAVEL_START_FROM",
    "travel_end_at": "TRAVEL_END_AT",
}

GUIDE_NOTES = """
## Notes for this form (Dienstreiseantrag Anlage 1, VwV-SächsRKG)
- `travel_start_from` / `travel_end_at` say where the trip starts and ends: `home-a`
  (main home), `home-b` (second home), `office` or `temporary-address`.
- Reason and explanation fields have a second line: `private_car_reason_continuation`,
  `flight_reason_continuation` and `explanations_continuation`.
- For "other" transport, tick `outbound_other_transport_selected` /
  `return_other_transport_selected` and name it in `outbound_other_transport` /
  `return_other_transport`.
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
    application_kind: Literal["business-trip", "training-trip", "it-trip"] | None = None,
    employment_status: Literal["civil-servant-or-judge", "employee", "temporary-civil-servant", "trainee"] | None = None,
    additional_participants: Literal["yes", "no"] | None = None,
    meal_provider: Literal["official", "personal"] | None = None,
    overnight_required: Literal["no", "yes"] | None = None,
    overnight_payment: Literal["free", "paid"] | None = None,
    overnight_provider: Literal["official", "personal"] | None = None,
    breakfast: Literal["with", "without"] | None = None,
    travel_start_from: Place | None = None,
    travel_end_at: Place | None = None,
    bahncard_class: Literal["second", "first"] | None = None,
    bahncard_rate: Literal["25", "50", "100"] | None = None,
) -> Path:
    """Fill applicant-editable fields in the business-trip application PDF.

    Args:
        departure_date: YYYY-MM-DD or DD.MM.YYYY, like all dates.
        departure_time: HH:MM (24h), like all times.
        travel_start_from: Where the trip starts: main home, second home, office or temporary address.
        travel_end_at: Where the trip ends: main home, second home, office or temporary address.
    """
    return fill(locals())


PARAMETERS = frozenset(inspect.signature(create_business_trip_application).parameters)


def fill(values: dict, output_path: str | Path | None = None, template_path: str | Path = TEMPLATE_PDF) -> Path:
    """Fill the form from a dict of `create_business_trip_application` arguments."""
    unknown = set(values) - PARAMETERS
    if unknown:
        raise TypeError(f"Unknown arguments for the {NAME} form: {', '.join(sorted(unknown))}.")
    values = with_env_defaults(values, ENV_DEFAULTS)
    check_trip_times(values)
    text, buttons = map_fields(values, TEXT_FIELDS, DATE_FORMATS, CHECKBOX_FIELDS, CHOICES)
    return fill_pdf(template_path, text, buttons, output_path)
