# Business Trip Application CLI

Fill the applicant-editable fields (sections 1–13) of `00_application-form.pdf` and save a completed PDF. Approval, accounting, and digital-signature fields are intentionally left for the responsible office and signers.

## Setup

```
git clone https://github.com/scads/
python -m pip install -r requirements.txt
```

Put reusable applicant details in `.env`:
```
SERVICE_UNIT=
APPLICANT_NAME=
DEPARTMENT=
OFFICE_PHONE=
HOME_ADDRESS=
ADDITIONAL_HOME_ADDRESS=
TEMPORARY_STAY_ADDRESS=
IBAN=
BIC=
BANK_NAME=
```
This file is ignored by Git because it may contain personal and banking information.

If you use this tool via an MCP-compatible AI-agent such as [Jan.AI](https://github.com/janhq/jan) (open source), it is recommended to use privacy-preserving, local-only Large Language Models. If you use a cloud-service for this, be aware that information such as your home adress and bank account might be shared with this cloud service provider!

## Use

```powershell
python business_trip.py --help
python business_trip.py `
  --application-kind business-trip `
  --destination "Dresden" `
  --purpose "Project meeting" `
  --departure-date 2026-10-12 `
  --outbound-train `
  --return-train `
  --output completed-trip.pdf
```

The CLI accepts options for all applicant-editable text fields, choices, and checkboxes. Omitted fields stay blank in the PDF. Boolean options support both `--option` and `--no-option`; radio choices are listed by `--help`.

The same function can be called from Python:

```python
from business_trip import create_business_trip_application

create_business_trip_application(
    "completed-trip.pdf",
    destination="Dresden",
    purpose="Project meeting",
    outbound_train=True,
)
```