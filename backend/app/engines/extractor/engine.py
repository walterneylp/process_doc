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
        text_norm = re.sub(r"[ \t]+", " ", text)

        def parse_brl_amount(raw: str) -> float | None:
            if raw is None:
                return None
            value = raw.strip()
            value = value.replace("R$", "").replace(" ", "")
            if "," in value:
                value = value.replace(".", "").replace(",", ".")
            try:
                return float(value)
            except ValueError:
                return None

        # número do documento
        doc_match = re.search(
            r"n[úu]mero\s+da\s+nfs-?e[^\d]{0,120}(\d{1,12})",
            text_norm,
            re.IGNORECASE | re.DOTALL,
        )
        if not doc_match:
            doc_match = re.search(r"(?:nota\s*fiscal|n[úu]mero|numero|doc(?:umento)?)[^\d]{0,80}(\d{3,})", text, re.IGNORECASE)
        if doc_match:
            output["document_number"] = doc_match.group(1)

        # CNPJ
        # Prioriza CNPJ formatado (com /), evitando capturar a chave de acesso.
        cnpj_match = re.search(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text)
        if not cnpj_match:
            cnpj_match = re.search(r"(\d{2}\d{3}\d{3}/\d{4}-\d{2})", text)
        if not cnpj_match:
            cnpj_match = re.search(r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", text)
        if cnpj_match:
            output["cnpj"] = re.sub(r"\D", "", cnpj_match.group(1))

        # CNPJ do tomador (quando presente na seção TOMADOR DO SERVIÇO).
        taker_section = re.search(
            r"tomador\s+do\s+servi[cç]o(.{0,900})",
            text_norm,
            re.IGNORECASE | re.DOTALL,
        )
        if taker_section:
            taker_cnpj_match = re.search(r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", taker_section.group(1))
            if taker_cnpj_match:
                output["taker_cnpj"] = re.sub(r"\D", "", taker_cnpj_match.group(1))

        # Chave de acesso NFS-e (normalmente 44 dígitos).
        access_key_match = re.search(
            r"chave\s+de\s+acesso\s+da\s+nfs-?e[^\d]{0,120}(\d{44,60})",
            text_norm,
            re.IGNORECASE | re.DOTALL,
        )
        if not access_key_match:
            access_key_match = re.search(r"\b(\d{44,60})\b", text_norm)
        if access_key_match:
            output["access_key_nfse"] = access_key_match.group(1)

        # Valor total
        amount_patterns = [
            r"valor\s+total\s+da\s+nfs-?e[^\d]{0,40}(R?\$?\s*[\d\.\,]+)",
            r"valor\s+l[íi]quido[^\d]{0,40}(R?\$?\s*[\d\.\,]+)",
            r"valor\s+dos\s+servi[cç]os[^\d]{0,40}(R?\$?\s*[\d\.\,]+)",
            r"(?:total|valor)[^\d]{0,30}(R?\$?\s*[\d\.\,]+)",
        ]
        amount_match = None
        for pattern in amount_patterns:
            amount_match = re.search(pattern, text_norm, re.IGNORECASE | re.DOTALL)
            if amount_match:
                break
        if amount_match:
            amount = parse_brl_amount(amount_match.group(1))
            if amount is not None:
                output["total_amount"] = amount

        services_match = re.search(
            r"valor\s+dos\s+servi[cç]os[^\d]{0,40}(R?\$?\s*[\d\.\,]+)",
            text_norm,
            re.IGNORECASE | re.DOTALL,
        )
        if services_match:
            amount = parse_brl_amount(services_match.group(1))
            if amount is not None:
                output["services_amount"] = amount

        iss_match = re.search(
            r"(?:valor\s+do\s+iss|\biss\b(?:\s+retido)?)[^\d]{0,40}(R?\$?\s*[\d\.\,]+)",
            text_norm,
            re.IGNORECASE | re.DOTALL,
        )
        if iss_match:
            amount = parse_brl_amount(iss_match.group(1))
            if amount is not None:
                output["iss_amount"] = amount

        # Data simples dd/mm/yyyy
        date_match = re.search(r"data\s+e\s+hora\s+da\s+emiss[aã]o[^\d]{0,30}(\d{2}/\d{2}/\d{4})", text_norm, re.IGNORECASE)
        if not date_match:
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if date_match:
            d, m, y = date_match.group(1).split("/")
            output["issue_date"] = f"{y}-{m}-{d}"

        return output
