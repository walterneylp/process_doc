from contextvars import ContextVar

current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)
