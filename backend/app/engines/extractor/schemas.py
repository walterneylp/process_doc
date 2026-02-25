GENERIC_DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "main_topic": {"type": "string"},
        "summary": {"type": "string"},
        "language": {"type": "string"},
    },
    "required": [],
}

TRAINING_CERT_SCHEMA = {
    "type": "object",
    "properties": {
        "trainee_name": {"type": "string"},
        "trainee_cpf": {"type": "string"},
        "company_name": {"type": "string"},
        "course_name": {"type": "string"},
        "workload_hours": {"type": "number"},
        "issue_date": {"type": "string"},
    },
    "required": ["trainee_name", "course_name"],
}

TRAINING_PRESENTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "course_name": {"type": "string"},
        "focus_area": {"type": "string"},
        "norm_references": {"type": "array", "items": {"type": "string"}},
        "target_audience": {"type": "string"},
    },
    "required": ["course_name"],
}

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "document_number": {"type": "string"},
        "issue_date": {"type": "string"},
        "total_amount": {"type": "number"},
        "cnpj": {"type": "string"},
        "taker_cnpj": {"type": "string"},
        "access_key_nfse": {"type": "string"},
        "iss_amount": {"type": "number"},
        "services_amount": {"type": "number"},
    },
    "required": ["document_number"],
}

DEFAULT_SCHEMA = GENERIC_DOCUMENT_SCHEMA


BUILTIN_SCHEMA_BY_DOC_TYPE = {
    "invoice": INVOICE_SCHEMA,
    "fiscal_xml": INVOICE_SCHEMA,
    "generic_document": GENERIC_DOCUMENT_SCHEMA,
    "training_certificate": TRAINING_CERT_SCHEMA,
    "training_presentation": TRAINING_PRESENTATION_SCHEMA,
}
