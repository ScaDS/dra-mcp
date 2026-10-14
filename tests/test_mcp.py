"""Checks the MCP server through an in-memory FastMCP client, once per form."""

import asyncio
import inspect

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import business_trip

FORM_NAMES = list(business_trip.FORMS)

TRIP = {
    "destination": "04109 Leipzig",
    "purpose": "Project meeting",
    "departure_date": "2026-10-12",
    "departure_time": "07:00",
    "business_start_date": "2026-10-12",
    "business_start_time": "09:00",
    "business_end_date": "2026-10-12",
    "business_end_time": "16:00",
    "return_date": "2026-10-12",
    "return_time": "18:30",
    "travel_start_from": "home-a",
    "travel_end_at": "home-a",
}


def server(form_name):
    # imported here so that the module-level server is built with the isolated test environment
    from business_trip_mcp_server import build_server

    return build_server(form_name)


def run(coroutine_function, form_name):
    async def session():
        async with Client(server(form_name)) as client:
            return await coroutine_function(client)

    return asyncio.run(session())


def enum_of(schema: dict) -> list | None:
    for option in schema.get("anyOf", [schema]):
        if "enum" in option:
            return option["enum"]
    return None


@pytest.mark.parametrize("form_name", FORM_NAMES)
def test_tool_schema_matches_the_form(form_name):
    form = business_trip.FORMS[form_name]
    tools = run(lambda client: client.list_tools(), form_name)

    assert [tool.name for tool in tools] == ["create_business_trip_application"]
    properties = tools[0].input_schema["properties"]
    assert set(properties) == set(inspect.signature(form.create_business_trip_application).parameters)
    assert "output_path" not in properties
    for argument, (_, labels) in form.CHOICES.items():
        assert enum_of(properties[argument]) == list(labels), argument
    assert form.TITLE in tools[0].description


@pytest.mark.parametrize("form_name", FORM_NAMES)
def test_tool_writes_the_pdf_to_output_dir(form_name, tmp_path):
    result = run(lambda client: client.call_tool("create_business_trip_application", TRIP), form_name)
    assert result.data == str(tmp_path / "output" / "business_trip_application_filled.pdf")
    assert (tmp_path / "output" / "business_trip_application_filled.pdf").exists()


@pytest.mark.parametrize("form_name", FORM_NAMES)
def test_invalid_choice_is_rejected_by_the_schema(form_name):
    with pytest.raises(ToolError, match="business-trip"):
        run(
            lambda client: client.call_tool(
                "create_business_trip_application", TRIP | {"application_kind": "Dienstreise"}
            ),
            form_name,
        )


def test_guide_uses_home_city_from_env(monkeypatch):
    monkeypatch.setenv("HOME_CITY", "Dresden")
    prompt = run(lambda client: client.get_prompt("business_trip_travel_planning_guide"), None)
    text = prompt.messages[0].content.text
    assert "The applicant is based in Dresden." in text
    assert "Leipzig" not in text.split("## Notes for this form")[0]


def test_form_is_selected_by_dra_form(monkeypatch):
    monkeypatch.setenv("DRA_FORM", "saxony")
    assert business_trip.get_form() is business_trip.FORMS["saxony"]
    monkeypatch.setenv("DRA_FORM", "unknown")
    with pytest.raises(ValueError, match="Unknown form 'unknown'"):
        business_trip.get_form()
