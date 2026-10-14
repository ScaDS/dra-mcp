"""Golden test: the Saxon form must be filled exactly as before the multi-form refactoring.

Regenerate the expected values with `UPDATE_GOLDEN=1 uv run pytest tests/test_saxony_golden.py`
only when a change of the filled values is intended.
"""

import json
import os
from pathlib import Path

from business_trip import create_business_trip_application_int
from pdf_helpers import field_values

GOLDEN_FILE = Path(__file__).with_name("golden_saxony.json")

SAMPLE = {
    "service_unit": "ScaDS.AI",
    "applicant_name": "Mustermann, Erika",
    "department": "Research",
    "office_phone": "0341 12345",
    "home_address": "Musterstraße 1, 04109 Leipzig",
    "additional_home_address": "Beispielweg 2, 01069 Dresden",
    "temporary_stay_address": "Gästehaus, 10115 Berlin",
    "destination": "80333 München",
    "purpose": "Project meeting",
    "overnight_cost_per_night": "85",
    "departure_date": "2026-10-11",
    "departure_time": "17:00",
    "business_start_date": "12.10.2026",
    "business_start_time": "09:00",
    "business_end_date": "2026-10-13",
    "business_end_time": "16:00",
    "return_date": "2026-10-13",
    "return_time": "21:30",
    "outbound_other_transport": "Taxi",
    "return_other_transport": "Fahrrad",
    "bahncard_number": "7081 1234",
    "bahncard_valid_until": "2027-03-31",
    "travel_card_from": "Leipzig",
    "travel_card_to": "Halle",
    "bonus_program_name": "bahn.bonus",
    "private_car_reason": "Equipment transport",
    "private_car_reason_continuation": "second line",
    "flight_reason": "Too far by train",
    "flight_reason_continuation": "second line",
    "private_stay_from": "2026-10-14",
    "private_stay_until": "2026-10-15",
    "private_stay_destination": "Nürnberg",
    "iban": "DE00000000000000000000",
    "bic": "TESTDEFFXXX",
    "bank_name": "Testbank",
    "explanations": "Costs partly covered by the host",
    "explanations_continuation": "second line",
    "application_date": "2026-10-08",
    "meals_provided_free": True,
    "outbound_train": True,
    "outbound_bus_or_public_transport": True,
    "outbound_private_car": False,
    "outbound_passenger_in_private_car": False,
    "outbound_official_car": False,
    "outbound_flight": False,
    "outbound_other_transport_selected": True,
    "return_train": True,
    "return_bus_or_public_transport": False,
    "return_private_car": False,
    "return_passenger_in_private_car": False,
    "return_official_car": False,
    "return_flight": False,
    "return_other_transport_selected": True,
    "uses_personal_travel_card": True,
    "participates_in_bonus_program": True,
    "requests_recognition_for_private_car": False,
    "has_field_service_role": False,
    "requests_flight_cost_reimbursement": False,
    "uses_official_air_miles": False,
    "requests_advance": True,
    "application_kind": "training-trip",
    "employment_status": "employee",
    "additional_participants": "no",
    "meal_provider": "personal",
    "overnight_required": "yes",
    "overnight_payment": "paid",
    "overnight_provider": "official",
    "breakfast": "without",
    "travel_start_from": "office",
    "travel_end_at": "home-b",
    "bahncard_class": "first",
    "bahncard_rate": "50",
}


def test_saxon_form_is_filled_as_before(tmp_path):
    output = create_business_trip_application_int(output_path=tmp_path / "filled.pdf", **SAMPLE)
    values = field_values(output)

    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN_FILE.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assert values == json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))
