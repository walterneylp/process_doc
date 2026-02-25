DEFAULT_SCHEMA = {
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
