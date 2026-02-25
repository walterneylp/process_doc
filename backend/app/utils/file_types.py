from pathlib import Path


def infer_doc_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".pdf"}:
        return "invoice"
    if suffix in {".xml"}:
        return "fiscal_xml"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return "scanned_document"
    if suffix in {".csv", ".xlsx"}:
        return "spreadsheet"
    return "generic_document"
