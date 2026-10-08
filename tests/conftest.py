import pytest

import business_trip

ENV_VARIABLES = (
    "SERVICE_UNIT",
    "APPLICANT_NAME",
    "DEPARTMENT",
    "OFFICE_PHONE",
    "HOME_ADDRESS",
    "ADDITIONAL_HOME_ADDRESS",
    "TEMPORARY_STAY_ADDRESS",
    "IBAN",
    "BIC",
    "BANK_NAME",
)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Keep the developer's real .env (name, address, IBAN) out of every test."""
    monkeypatch.setattr(business_trip, "ENV_FILE", tmp_path / "missing.env")
    for variable in ENV_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

