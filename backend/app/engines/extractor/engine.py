import re

from sqlalchemy.orm import Session

from backend.app.adapters.llm.openai_provider import OpenAIProvider
from backend.app.db import models
from backend.app.engines.extractor.schemas import BUILTIN_SCHEMA_BY_DOC_TYPE, DEFAULT_SCHEMA
from backend.app.utils.jsonschema import validate_json_schema


class ExtractionEngine:
    def __init__(self):
        self.provider = OpenAIProvider()

    def schema_for(self, db: Session, tenant_id, doc_type: str) -> dict:
        return self._schema_for(db, tenant_id, doc_type)

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
        if item:
            return item.schema
        return BUILTIN_SCHEMA_BY_DOC_TYPE.get(doc_type, DEFAULT_SCHEMA)

    def extract(self, db: Session, tenant_id, doc_type: str, content: str) -> dict:
        schema = self._schema_for(db, tenant_id, doc_type)
        prompt = f"Extraia dados e retorne JSON válido para schema: {schema}. Conteúdo: {content}"

        for _ in range(2):
            payload = self.provider.extract(prompt)
            ok, err = validate_json_schema(payload, schema)
            if ok:
                return payload
        local_payload = self._local_extract(content, doc_type)
        ok, err = validate_json_schema(local_payload, schema)
        if ok:
            return local_payload
        raise ValueError(f"invalid_extraction_schema: {err}")

    def _local_extract(self, content: str, doc_type: str | None = None) -> dict:
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

        if doc_type == "training_certificate":
            # Nome do participante entre "Certificamos que" e "participou".
            trainee_match = re.search(
                r"certificamos\s+que\s+([A-ZÀ-Ú\s]+?)\s+participou",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if trainee_match:
                output["trainee_name"] = re.sub(r"\s+", " ", trainee_match.group(1)).strip()
            if "trainee_name" not in output:
                filename_name_match = re.search(
                    r"(?:cert(?:ificado)?[-_\s]*nr-?10)[\s\-_:]+([A-ZÀ-Ú\s]+?)[\s\-_:]+\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
                    text,
                    re.IGNORECASE,
                )
                if filename_name_match:
                    output["trainee_name"] = re.sub(r"\s+", " ", filename_name_match.group(1)).strip().upper()

            cpf_match = re.search(r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b", text)
            if cpf_match:
                output["trainee_cpf"] = re.sub(r"\D", "", cpf_match.group(1))

            course_match = re.search(
                r"participou\s+do\s+treinamento\s+(.+?)\s+em\s+conformidade",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if course_match:
                output["course_name"] = re.sub(r"\s+", " ", course_match.group(1)).strip()
            if "course_name" not in output and re.search(r"\bnr-?10\b", text, re.IGNORECASE):
                output["course_name"] = "NR-10 - Básico"

            hours_match = re.search(r"carga\s+hor[áa]ria\s+de\s+(\d+)\s+horas", text_norm, re.IGNORECASE)
            if hours_match:
                output["workload_hours"] = float(hours_match.group(1))

            # Empresa: linha textual imediatamente antes do CNPJ empresarial.
            company_match = re.search(
                r"\n([A-Z0-9À-Ú][A-Z0-9À-Ú\s\.-]{5,})\n\s*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
                text,
                re.IGNORECASE,
            )
            if company_match:
                value = re.sub(r"\s+", " ", company_match.group(1)).strip()
                if not re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", value):
                    output["company_name"] = value

            # Para certificado, não obrigar campos de NF.
            for field in ["document_number", "cnpj", "taker_cnpj", "access_key_nfse", "iss_amount", "services_amount", "total_amount"]:
                output.pop(field, None)

        return output
