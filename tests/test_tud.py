"""Checks specific to the TU Dresden form (RK-02): schedule grid, date formats, purpose length."""

import asyncio
import re

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from pypdf import PdfReader

import form_tud
from pdf_helpers import field_values

SCHEDULE = {
    "departure_date": "2026-10-11",
    "departure_time": "17:00",
    "business_start_date": "2026-10-12",
    "business_start_time": "09:00",
    "business_end_date": "13.10.2026",
    "business_end_time": "16:00",
    "return_date": "2026-10-13",
    "return_time": "21:30",
}
EXPECTED_CELLS = {
    "departure_date": "11.10.26",
    "departure_time": "17:00",
    "business_start_date": "12.10.26",
    "business_start_time": "09:00",
    "business_end_date": "13.10.26",
    "business_end_time": "16:00",
}
GRID_FIELDS = {name for row in form_tud.SCHEDULE_ROWS.values() for name in row.values()}
ROWS = list(form_tud.SCHEDULE_ROWS)


def widgets(template=form_tud.TEMPLATE_PDF) -> dict[str, dict]:
    """Return rectangle and date format script of each terminal field's first widget."""
    result = {}
    for page in PdfReader(template).pages:
        for annotation in page.get("/Annots") or []:
            widget = annotation.get_object()
            field = widget if "/T" in widget else widget["/Parent"].get_object()
            actions = widget.get("/AA") or field.get("/AA") or {}
            script = actions["/F"].get_object().get("/JS") if "/F" in actions else None
            if script is not None and hasattr(script.get_object(), "get_data"):
                script = script.get_object().get_data().decode("latin-1")
            match = re.search(r'AFDate_FormatEx\("([^"]+)"\)', str(script or ""))
            result.setdefault(
                field["/T"],
                {"rect": [float(value) for value in widget["/Rect"]], "date_format": match and match.group(1)},
            )
    return result


@pytest.mark.parametrize("start", ROWS)
@pytest.mark.parametrize("end", ROWS)
def test_schedule_is_placed_in_the_start_and_end_rows(start, end):
    values = field_values(form_tud.fill(SCHEDULE | {"travel_start_from": start, "travel_end_at": end}))

    start_row, end_row = form_tud.SCHEDULE_ROWS[start], form_tud.SCHEDULE_ROWS[end]
    expected = {start_row[cell]: value for cell, value in EXPECTED_CELLS.items()}
    expected |= {end_row["return_date"]: "13.10.26", end_row["return_time"]: "21:30"}
    expected |= {start_row["start_box"]: "/Ja", end_row["end_box"]: "/Ja"}
    filled_grid = {name: value for name, value in values.items() if name in GRID_FIELDS and value != "/Off"}
    assert filled_grid == expected


def test_schedule_rows_default_to_env(monkeypatch):
    monkeypatch.setenv("TRAVEL_START_FROM", "office")
    monkeypatch.setenv("TRAVEL_END_AT", "home-b")
    values = field_values(form_tud.fill(SCHEDULE))
    assert values["Datum Beginn Reise Dienststelle_af_date"] == "11.10.26"
    assert values["Datum Ende Reise Wohnung B"] == "13.10.26"


def test_missing_schedule_row_asks_for_it():
    with pytest.raises(ValueError, match="travel_start_from is needed .* Ask the user where the trip starts"):
        form_tud.fill(SCHEDULE | {"travel_end_at": "home-a"})
    with pytest.raises(ValueError, match="travel_end_at is needed .* Ask the user where the trip ends"):
        form_tud.fill(SCHEDULE | {"travel_start_from": "home-a"})


def test_no_schedule_row_needed_without_schedule_values():
    values = field_values(form_tud.fill({"destination": "Leipzig"}))
    assert values["Reiseziele"] == "Leipzig"


def test_invalid_schedule_row_from_env_is_rejected(monkeypatch):
    monkeypatch.setenv("TRAVEL_START_FROM", "home")
    with pytest.raises(ValueError, match="travel_start_from must be one of: home-a, home-b"):
        form_tud.fill(SCHEDULE | {"travel_end_at": "home-a"})


def test_purpose_must_fit_on_one_line():
    form_tud.fill({"purpose": "x" * form_tud.PURPOSE_MAX_LENGTH})
    with pytest.raises(ValueError, match="purpose has 71 characters"):
        form_tud.fill({"purpose": "x" * (form_tud.PURPOSE_MAX_LENGTH + 1)})


def test_date_formats_match_the_scripts_in_the_pdf():
    scripts = {"dd.mm.yy": "%d.%m.%y", "dd.mm.yyyy": "%d.%m.%Y", None: "%d.%m.%Y"}
    fields = widgets()
    for argument, date_format in form_tud.DATE_FORMATS.items():
        assert scripts[fields[form_tud.TEXT_FIELDS[argument]]["date_format"]] == date_format, argument
    for row in form_tud.SCHEDULE_ROWS.values():
        for cell in ("departure_date", "business_start_date", "business_end_date", "return_date"):
            assert scripts[fields[row[cell]]["date_format"]] == form_tud.SCHEDULE_DATE_FORMAT, row[cell]


def test_schedule_rows_match_the_grid_layout():
    """Each row's fields share one line, ordered left to right like the printed columns."""
    fields = widgets()
    row_heights = []
    for name, row in form_tud.SCHEDULE_ROWS.items():
        rects = [fields[field]["rect"] for field in row.values()]
        middles = [(rect[1] + rect[3]) / 2 for rect in rects]
        assert max(middles) - min(middles) < 5, name
        lefts = [rect[0] for rect in rects]
        assert lefts == sorted(lefts), name
        row_heights.append(sum(middles) / len(middles))
    assert row_heights == sorted(row_heights, reverse=True)


def test_mcp_schema_has_the_tud_fields_and_options():
    from business_trip_mcp_server import build_server

    async def list_tools():
        async with Client(build_server("tud")) as client:
            return await client.list_tools()

    properties = asyncio.run(list_tools())[0].input_schema["properties"]
    assert {"personnel_number", "outbound_rental_car", "bahncard_type"} <= set(properties)
    assert {"has_field_service_role", "outbound_other_transport", "explanations_continuation"}.isdisjoint(properties)
    kinds = next(option["enum"] for option in properties["application_kind"]["anyOf"] if "enum" in option)
    assert kinds == ["business-trip", "third-party-interest-trip", "training-trip"]


def test_mcp_tool_reports_a_missing_schedule_row():
    from business_trip_mcp_server import build_server

    async def call():
        async with Client(build_server("tud")) as client:
            return await client.call_tool("create_business_trip_application", {"destination": "Leipzig", "purpose": "Meeting", **SCHEDULE})

    with pytest.raises(ToolError, match="Ask the user where the trip starts"):
        asyncio.run(call())
