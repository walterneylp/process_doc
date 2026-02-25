DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "document_number": {"type": "string"},
        "issue_date": {"type": "string"},
        "total_amount": {"type": "number"},
        "cnpj": {"type": "string"},
    },
    "required": ["document_number"],
}
