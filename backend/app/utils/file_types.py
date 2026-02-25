from pathlib import Path


def infer_doc_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    name = Path(filename).name.lower()

    certificate_keywords = ["cert", "certificado"]
    presentation_keywords = ["apresentacao", "apresentação", "treinamento", "aula", "material", "slides", "sep"]
    invoice_keywords = ["nfe", "nf-e", "nfse", "nota", "danfe", "fatura", "boleto", "invoice"]

    if any(k in name for k in certificate_keywords):
        return "training_certificate"
    if any(k in name for k in presentation_keywords):
        return "training_presentation"
    if any(k in name for k in invoice_keywords):
        return "invoice"

    if suffix in {".pdf"}:
        return "generic_document"
    if suffix in {".xml"}:
        return "fiscal_xml"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return "scanned_document"
    if suffix in {".csv", ".xlsx"}:
        return "spreadsheet"
    return "generic_document"
