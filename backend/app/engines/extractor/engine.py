import re

from sqlalchemy.orm import Session

from backend.app.adapters.llm.openai_provider import OpenAIProvider
from backend.app.db import models
from backend.app.engines.extractor.schemas import DEFAULT_SCHEMA
from backend.app.utils.jsonschema import validate_json_schema


class ExtractionEngine:
    def __init__(self):
        self.provider = OpenAIProvider()

    def _schema_for(self, db: Session, tenant_id, doc_type: str) -> dict:
        item = (
            db.query(models.ExtractionSchema)
            .filter(
                models.ExtractionSchema.tenant_id == tenant_id,
                models.ExtractionSchema.doc_type == doc_type,
                models.ExtractionSchema.is_active == True,
            )
            .first()
        )
        return item.schema if item else DEFAULT_SCHEMA

    def extract(self, db: Session, tenant_id, doc_type: str, content: str) -> dict:
        schema = self._schema_for(db, tenant_id, doc_type)
        prompt = f"Extraia dados e retorne JSON válido para schema: {schema}. Conteúdo: {content}"

        for _ in range(2):
            payload = self.provider.extract(prompt)
            ok, err = validate_json_schema(payload, schema)
            if ok:
                return payload
        local_payload = self._local_extract(content)
        ok, err = validate_json_schema(local_payload, schema)
        if ok:
            return local_payload
        raise ValueError(f"invalid_extraction_schema: {err}")

    def _local_extract(self, content: str) -> dict:
        text = content or ""
        output: dict = {}

        # número do documento
        doc_match = re.search(r"(?:nota\s*fiscal|n[úu]mero|numero|doc(?:umento)?)[^\d]{0,20}(\d{3,})", text, re.IGNORECASE)
        if doc_match:
            output["document_number"] = doc_match.group(1)

        # CNPJ
        cnpj_match = re.search(r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", text)
        if cnpj_match:
            output["cnpj"] = re.sub(r"\D", "", cnpj_match.group(1))

        # Valor total
        amount_match = re.search(r"(?:total|valor)[^\d]{0,20}(\d+[\.,]\d{2})", text, re.IGNORECASE)
        if amount_match:
            output["total_amount"] = float(amount_match.group(1).replace(".", "").replace(",", "."))

        # Data simples dd/mm/yyyy
        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if date_match:
            d, m, y = date_match.group(1).split("/")
            output["issue_date"] = f"{y}-{m}-{d}"

        return output
