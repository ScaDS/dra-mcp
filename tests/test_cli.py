import pytest

import business_trip
from pdf_helpers import field_values

ARGUMENTS = [
    "--application-kind", "business-trip",
    "--destination", "Dresden",
    "--purpose", "Project meeting",
    "--departure-date", "2026-10-12",
    "--outbound-train",
    "--no-return-train",
]


def test_cli_fills_the_form_without_opening_it(tmp_path, monkeypatch, capsys):
    opened = []
    monkeypatch.setattr(business_trip, "open_file", opened.append)
    output = tmp_path / "completed-trip.pdf"

    assert business_trip.main([*ARGUMENTS, "--output", str(output), "--no-open"]) == 0

    assert opened == []
    assert f"written to {output}" in capsys.readouterr().out
    values = field_values(output)
    assert values["Antragsteller.reiseziel"] == "Dresden"
    assert values["dat1"] == "12.10.2026"
    assert values["kk7.1"] == "/ja"
    assert values["kk7.1a"] == "/Off"


def test_cli_opens_the_filled_pdf_by_default(tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(business_trip, "open_file", opened.append)

    business_trip.main(ARGUMENTS)

    assert opened == [tmp_path / "output" / "business_trip_application_filled.pdf"]


def test_cli_rejects_unknown_choice(capsys):
    with pytest.raises(SystemExit):
        business_trip.main(["--application-kind", "Dienstreise"])
    assert "invalid choice" in capsys.readouterr().err


def test_old_python_api_still_works(tmp_path):
    output = business_trip.create_business_trip_application_int(
        output_path=tmp_path / "trip.pdf", destination="Dresden", outbound_train=True
    )
    assert field_values(output)["Antragsteller.reiseziel"] == "Dresden"


def test_names_of_the_former_module_are_still_importable():
    from business_trip import (  # noqa: F401
        BASE_DIR,
        CHECKBOX_FIELDS,
        DATE_FIELDS,
        DEFAULT_OUTPUT,
        ENV_DEFAULTS,
        ENV_FILE,
        RADIO_OPTIONS,
        TEMPLATE_PDF,
        TEXT_FIELDS,
        build_parser,
        create_business_trip_application,
        create_business_trip_application_int,
        format_date,
        main,
        parse_datetime,
    )

    assert DATE_FIELDS == {
        "departure_date",
        "business_start_date",
        "business_end_date",
        "return_date",
        "bahncard_valid_until",
        "private_stay_from",
        "private_stay_until",
        "application_date",
    }
    # the shape and values the module had before the multi-form refactoring
    assert RADIO_OPTIONS == {
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
        "travel_start_from": ("beginn", {"home-a": 1, "home-b": 2, "office": 3, "temporary-address": 4}),
        "travel_end_at": ("ende", {"home-a": 1, "home-b": 2, "office": 3, "temporary-address": 4}),
        "bahncard_class": ("BC_2_1", {"second": 1, "first": 2}),
        "bahncard_rate": ("bcklasse", {"25": 1, "50": 2, "100": 3}),
    }
