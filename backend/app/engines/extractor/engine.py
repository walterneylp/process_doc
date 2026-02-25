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
        raise ValueError(f"invalid_extraction_schema: {err}")
