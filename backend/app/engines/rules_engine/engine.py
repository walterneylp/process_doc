from dataclasses import dataclass


@dataclass
class RuleResult:
    category: str
    department: str
    confidence: float
    priority: str
    reason: str


class RulesEngine:
    def classify(self, sender: str, subject: str, attachment_name: str | None = None) -> RuleResult:
        sender_l = (sender or "").lower()
        subject_l = (subject or "").lower()
        attachment_l = (attachment_name or "").lower()

        if "nota fiscal" in subject_l or attachment_l.endswith(".xml"):
            return RuleResult("fiscal", "financeiro", 0.92, "high", "keyword_nota_fiscal")
        if sender_l.endswith("@banco.com"):
            return RuleResult("financeiro", "financeiro", 0.87, "high", "sender_domain")
        if attachment_l.endswith(".pdf"):
            return RuleResult("documento_pdf", "operacoes", 0.78, "normal", "attachment_pdf")
        return RuleResult("geral", "triage", 0.4, "normal", "default")
