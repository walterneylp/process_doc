from backend.app.db import models


def can_process_email(plan: models.Plan, usage: models.TenantUsage) -> bool:
    if plan.monthly_email_limit is None:
        return True
    return usage.emails_processed < plan.monthly_email_limit


def can_call_llm(plan: models.Plan, usage: models.TenantUsage) -> bool:
    if plan.monthly_llm_calls_limit is None:
        return True
    return usage.llm_calls < plan.monthly_llm_calls_limit
