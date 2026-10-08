from pypdf import PdfReader


def field_values(path) -> dict[str, str]:
    """Return the /V value of every filled form field in a PDF."""
    fields = PdfReader(path).get_fields() or {}
    return {name: str(field["/V"]) for name, field in fields.items() if field.get("/V") is not None}


def inconsistent_buttons(path) -> list[str]:
    """Return checkbox/radio widgets whose shown state (/AS) disagrees with the field value (/V)."""
    problems = []
    for page in PdfReader(path).pages:
        for annotation in page.get("/Annots") or []:
            widget = annotation.get_object()
            if "/AS" not in widget:
                continue
            field = widget if "/V" in widget or "/Parent" not in widget else widget["/Parent"].get_object()
            value = field.get("/V")
            if widget["/AS"] != "/Off" and widget["/AS"] != value:
                problems.append(f"{field.get('/T')}: /AS {widget['/AS']} but /V {value}")
            on_states = [state for state in widget["/AP"]["/N"] if state != "/Off"]
            if value in on_states and widget["/AS"] != value:
                problems.append(f"{field.get('/T')}: /V {value} but widget shows {widget['/AS']}")
    return problems
