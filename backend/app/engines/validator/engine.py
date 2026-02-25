import re
from datetime import datetime


class ValidatorEngine:
    cnpj_pattern = re.compile(r"^\d{14}$")

    def validate(self, data: dict) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if "issue_date" in data:
            try:
                datetime.fromisoformat(str(data["issue_date"]).replace("Z", "+00:00"))
            except ValueError:
                errors.append("invalid_issue_date")

        if "total_amount" in data:
            try:
                float(data["total_amount"])
            except (TypeError, ValueError):
                errors.append("invalid_total_amount")
        for numeric_field in ["iss_amount", "services_amount"]:
            if numeric_field in data:
                try:
                    float(data[numeric_field])
                except (TypeError, ValueError):
                    errors.append(f"invalid_{numeric_field}")

        if "cnpj" in data and data["cnpj"] is not None:
            clean = re.sub(r"\D", "", str(data["cnpj"]))
            if not self.cnpj_pattern.match(clean):
                errors.append("invalid_cnpj")
        if "taker_cnpj" in data and data["taker_cnpj"] is not None:
            clean = re.sub(r"\D", "", str(data["taker_cnpj"]))
            if not self.cnpj_pattern.match(clean):
                errors.append("invalid_taker_cnpj")
        if "access_key_nfse" in data and data["access_key_nfse"] is not None:
            access = re.sub(r"\D", "", str(data["access_key_nfse"]))
            if len(access) < 44 or len(access) > 60:
                errors.append("invalid_access_key_nfse")

        for field in ["document_number"]:
            if field not in data:
                errors.append(f"missing_{field}")

        return len(errors) == 0, errors
