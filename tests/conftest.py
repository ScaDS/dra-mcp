import pytest

import pdf_form

ENV_VARIABLES = (
    "SERVICE_UNIT",
    "APPLICANT_NAME",
    "PERSONNEL_NUMBER",
    "DEPARTMENT",
    "OFFICE_PHONE",
    "HOME_ADDRESS",
    "ADDITIONAL_HOME_ADDRESS",
    "TEMPORARY_STAY_ADDRESS",
    "IBAN",
    "BIC",
    "BANK_NAME",
    "TRAVEL_START_FROM",
    "TRAVEL_END_AT",
    "DRA_FORM",
    "HOME_CITY",
    "OUTPUT_DIR",
)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Keep the developer's real .env (name, address, IBAN) out of every test and write PDFs to tmp_path."""
    monkeypatch.setattr(pdf_form, "ENV_FILE", tmp_path / "missing.env")
    for variable in ENV_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "output"))
