"""Checks every form module against its PDF template and the shared filling rules."""

import inspect

import pytest
from pypdf import PdfReader

import business_trip
from business_trip import literal_choices
from pdf_form import button_states
from pdf_helpers import field_values, inconsistent_buttons

FORMS = list(business_trip.FORMS.values())
form_param = pytest.mark.parametrize("form", FORMS, ids=[form.NAME for form in FORMS])

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


def mapped_fields(form) -> set[str]:
    fields = set(form.TEXT_FIELDS.values()) | set(form.CHECKBOX_FIELDS.values())
    fields |= {pdf_field for pdf_field, _ in form.CHOICES.values()}
    for row in getattr(form, "SCHEDULE_ROWS", {}).values():
        fields |= set(row.values())
    return fields


@form_param
def test_every_mapped_field_exists_in_the_template(form):
    template_fields = set(PdfReader(form.TEMPLATE_PDF).get_fields())
    assert mapped_fields(form) - template_fields == set()


@form_param
def test_every_mapped_argument_is_a_parameter(form):
    parameters = set(inspect.signature(form.create_business_trip_application).parameters)
    arguments = set(form.TEXT_FIELDS) | set(form.CHECKBOX_FIELDS) | set(form.CHOICES) | set(form.ENV_DEFAULTS)
    assert arguments - parameters == set()


@form_param
def test_choice_labels_match_the_options_in_the_pdf(form):
    states = button_states(PdfReader(form.TEMPLATE_PDF))
    for argument, (pdf_field, labels) in form.CHOICES.items():
        assert set(labels.values()) == set(states[pdf_field]), argument


@form_param
def test_checkboxes_have_exactly_one_on_state(form):
    states = button_states(PdfReader(form.TEMPLATE_PDF))
    for argument, pdf_field in form.CHECKBOX_FIELDS.items():
        assert len(states[pdf_field]) == 1, argument


@form_param
def test_literal_types_match_the_choices(form):
    parameters = inspect.signature(form.create_business_trip_application).parameters
    for argument, (_, labels) in form.CHOICES.items():
        assert literal_choices(parameters[argument].annotation) == tuple(labels), argument


@form_param
def test_filled_buttons_show_their_values(form):
    output = form.fill(
        {**TRIP, **dict.fromkeys(form.CHECKBOX_FIELDS, True)}
        | {argument: next(iter(labels)) for argument, (_, labels) in form.CHOICES.items()}
    )
    assert inconsistent_buttons(output) == []


@form_param
def test_unknown_arguments_are_rejected(form):
    with pytest.raises(TypeError, match="destinaton"):
        form.fill({"destinaton": "Berlin"})


@form_param
def test_invalid_choice_lists_the_valid_values(form):
    with pytest.raises(ValueError, match="business-trip"):
        form.fill({"application_kind": "Dienstreise"})


@form_param
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"departure_time": "09:30"}, "Departure date/time must be before business start"),
        ({"business_end_time": "08:00"}, "Business start date/time must not be after business end"),
        ({"return_time": "15:00"}, "Return date/time must be after business end"),
        ({"departure_time": "7 Uhr"}, "Departure time must use HH:MM"),
        ({"departure_time": "07:0"}, "Departure time must use HH:MM"),
        ({"return_time": "25:00"}, "Return time must use HH:MM"),
        ({"return_date": "12/10/2026"}, "Return date must use YYYY-MM-DD"),
    ],
)
def test_trip_times_are_checked(form, changes, message):
    with pytest.raises(ValueError, match=message):
        form.fill(TRIP | changes)


@form_param
@pytest.mark.parametrize("time_value", ["7 Uhr", "07:0", "7"])
def test_each_time_is_checked_even_without_the_rest_of_the_trip(form, time_value):
    with pytest.raises(ValueError, match="Departure time must use HH:MM"):
        form.fill({"departure_time": time_value})


@form_param
def test_times_are_written_as_hh_mm(form):
    output = form.fill(TRIP | {"departure_time": "7:05"})
    assert "07:05" in field_values(output).values()


@form_param
def test_business_may_start_and_end_at_the_same_time(form):
    form.fill(TRIP | {"business_end_time": "09:00"})


@form_param
def test_output_goes_to_output_dir_without_overwriting(form, tmp_path):
    first = form.fill(TRIP)
    second = form.fill(TRIP)
    assert first == tmp_path / "output" / "business_trip_application_filled.pdf"
    assert second == tmp_path / "output" / "business_trip_application_filled-1.pdf"


@form_param
def test_personal_details_come_from_env(form, monkeypatch):
    monkeypatch.setenv("APPLICANT_NAME", "Mustermann, Erika")
    monkeypatch.setenv("IBAN", "DE00000000000000000000")
    values = field_values(form.fill(TRIP))
    assert values[form.TEXT_FIELDS["applicant_name"]] == "Mustermann, Erika"
    assert values[form.TEXT_FIELDS["iban"]] == "DE00000000000000000000"
