from pypdf import PdfReader


def field_values(path) -> dict[str, str]:
    """Return the /V value of every filled form field in a PDF."""
    fields = PdfReader(path).get_fields() or {}
    return {name: str(field["/V"]) for name, field in fields.items() if field.get("/V") is not None}
