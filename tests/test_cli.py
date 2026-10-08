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
