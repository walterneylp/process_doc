import uuid

from sqlalchemy.orm import Session

from backend.app.adapters.email.imap_client import ImapClientAdapter
from backend.app.adapters.notify.email_notify import EmailNotifyAdapter
from backend.app.core.limits import can_call_llm, can_process_email
from backend.app.db.models import (
    Classification,
    DeadLetter,
    Document,
    Email,
    EmailAccount,
    EmailAttachment,
    Extraction,
    Plan,
    Tenant,
    TenantRule,
)
from backend.app.db.session import SessionLocal
from backend.app.domain.audit.service import log_event
from backend.app.domain.billing.service import get_or_create_usage
from backend.app.domain.document.service import create_document_from_attachment
from backend.app.domain.email.service import create_email_attachment, create_email_if_missing
from backend.app.adapters.storage.local import LocalStorageAdapter
from backend.app.engines.extractor.engine import ExtractionEngine
from backend.app.engines.llm_classifier.engine import LLMClassifierEngine
from backend.app.engines.rules_engine.engine import RulesEngine
from backend.app.engines.validator.engine import ValidatorEngine
from backend.app.utils.document_text import extract_text_from_file
from backend.app.workers.celery_app import celery_app


def _tenant_plan(db: Session, tenant_id):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    return db.query(Plan).filter(Plan.name == "Starter").first()


@celery_app.task(name="backend.app.workers.tasks.sync_all_accounts")
def sync_all_accounts() -> None:
    db = SessionLocal()
    try:
        accounts = db.query(EmailAccount).filter(EmailAccount.is_active == True).all()
        for account in accounts:
            sync_email_account.delay(str(account.id))
    finally:
        db.close()


@celery_app.task(name="backend.app.workers.tasks.sync_email_account")
def sync_email_account(account_id: str) -> None:
    db = SessionLocal()
    try:
        account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            return

        client = ImapClientAdapter(
            host=account.imap_host,
            port=account.imap_port,
            username=account.imap_username,
            password_enc=account.imap_password_enc,
            use_ssl=account.use_ssl,
        )
        messages = client.fetch_recent()

        for msg in messages:
            msg["trace_id"] = uuid.uuid4().hex
            email = create_email_if_missing(db, account.tenant_id, account.id, msg)
            if email:
                storage = LocalStorageAdapter()
                for att in msg.get("attachments", []):
                    filename = (att.get("filename") or "attachment.bin").strip() or "attachment.bin"
                    file_path, sha256 = storage.save_attachment(
                        str(account.tenant_id),
                        str(email.id),
                        filename,
                        att.get("content", b""),
                    )
                    create_email_attachment(
                        db=db,
                        tenant_id=account.tenant_id,
                        email_id=email.id,
                        filename=filename,
                        mime_type=att.get("mime_type"),
                        file_path=file_path,
                        sha256=sha256,
                    )
                process_email.delay(str(email.id))
                log_event(
                    db,
                    tenant_id=account.tenant_id,
                    trace_id=email.trace_id,
                    event_type="ingestao",
                    entity_type="email",
                    entity_id=str(email.id),
                    payload={"message_id": email.message_id},
                )
    finally:
        db.close()


@celery_app.task(name="backend.app.workers.tasks.process_email")
def process_email(email_id: str) -> None:
    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return

        plan = _tenant_plan(db, email.tenant_id)
        usage = get_or_create_usage(db, email.tenant_id)
        if plan and not can_process_email(plan, usage):
            email.status = "FAILED"
            db.commit()
            return

        attachments = db.query(EmailAttachment).filter(EmailAttachment.email_id == email.id).all()
        created_docs = 0
        if attachments:
            for attachment in attachments:
                doc = create_document_from_attachment(
                    db=db,
                    tenant_id=email.tenant_id,
                    email_id=email.id,
                    attachment_id=attachment.id,
                    filename=attachment.filename or "attachment",
                    trace_id=email.trace_id,
                )
                doc.status = "PROCESSING"
                db.commit()
                process_document.delay(str(doc.id))
                created_docs += 1

        # Fallback: processa com o conteúdo do corpo quando não há anexo.
        if created_docs == 0:
            doc = Document(
                tenant_id=email.tenant_id,
                email_id=email.id,
                attachment_id=None,
                doc_type="generic_document",
                status="PROCESSING",
                trace_id=email.trace_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            process_document.delay(str(doc.id))

        email.status = "PROCESSING"
        db.commit()
    finally:
        db.close()


@celery_app.task(name="backend.app.workers.tasks.process_document")
def process_document(document_id: str) -> None:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        email = db.query(Email).filter(Email.id == doc.email_id).first()
        if not email:
            return

        attachment = None
        attachment_text = ""
        attachment_name = None
        if doc.attachment_id:
            attachment = db.query(EmailAttachment).filter(EmailAttachment.id == doc.attachment_id).first()
            if attachment:
                attachment_name = attachment.filename
                attachment_text = extract_text_from_file(attachment.file_path, attachment.mime_type)

        context_chunks = [
            f"Assunto: {email.subject or ''}",
            f"Remetente: {email.sender or ''}",
            f"Corpo: {email.body_text or ''}",
            f"Texto do anexo: {attachment_text}",
        ]
        analysis_content = "\n\n".join(chunk for chunk in context_chunks if chunk.strip())

        plan = _tenant_plan(db, doc.tenant_id)
        usage = get_or_create_usage(db, doc.tenant_id)

        rules_engine = RulesEngine()
        llm_engine = LLMClassifierEngine()
        extraction_engine = ExtractionEngine()
        validator = ValidatorEngine()

        rr = rules_engine.classify(email.sender or "", email.subject or "", attachment_name)
        if rr.confidence >= 0.85:
            result = {
                "category": rr.category,
                "department": rr.department,
                "confidence": rr.confidence,
                "priority": rr.priority,
                "reason": rr.reason,
                "source": "rules",
            }
        else:
            if plan and not can_call_llm(plan, usage):
                doc.status = "FAILED"
                db.commit()
                return
            payload = llm_engine.classify(email.subject or "", email.sender or "", analysis_content)
            usage.llm_calls += 1
            result = {**payload, "source": "llm"}

        classification = Classification(
            tenant_id=doc.tenant_id,
            document_id=doc.id,
            category=result["category"],
            department=result["department"],
            confidence=result["confidence"],
            priority=result["priority"],
            reason=result["reason"],
            source=result["source"],
        )
        db.add(classification)
        db.flush()

        extracted = extraction_engine.extract(db, doc.tenant_id, doc.doc_type or "generic_document", analysis_content)
        extraction = Extraction(tenant_id=doc.tenant_id, document_id=doc.id, data=extracted)
        db.add(extraction)

        valid, errors = validator.validate(extracted)
        confidence = float(result.get("confidence", 0))
        if confidence < 0.75 and "low_confidence" not in errors:
            errors.append("low_confidence")
        if not valid:
            doc.needs_review = True
            db.add(
                DeadLetter(
                    tenant_id=doc.tenant_id,
                    entity_type="document",
                    entity_id=str(doc.id),
                    reason=",".join(errors),
                    payload={"errors": errors},
                    trace_id=doc.trace_id,
                )
            )
        elif confidence < 0.75:
            doc.needs_review = True

        routing = (
            db.query(TenantRule)
            .filter(TenantRule.tenant_id == doc.tenant_id, TenantRule.is_active == True)
            .first()
        )
        notify_emails = []
        if routing and routing.definition:
            notify_emails = routing.definition.get("emails", [])
        EmailNotifyAdapter().send(
            recipients=notify_emails,
            subject=f"Novo documento {classification.category}",
            body=f"Documento {doc.id} prioridade {classification.priority}",
        )

        doc.status = "DONE"
        usage.emails_processed += 1
        email.status = "DONE"
        db.commit()

        log_event(
            db,
            tenant_id=doc.tenant_id,
            trace_id=doc.trace_id,
            event_type="pipeline_done",
            entity_type="document",
            entity_id=str(doc.id),
            payload={"classification": classification.category},
        )
    except Exception as exc:
        db.rollback()
        item = db.query(Document).filter(Document.id == document_id).first()
        if item:
            item.status = "FAILED"
            db.add(
                DeadLetter(
                    tenant_id=item.tenant_id,
                    entity_type="document",
                    entity_id=str(item.id),
                    reason=str(exc),
                    payload=None,
                    trace_id=item.trace_id,
                )
            )
            db.commit()
    finally:
        db.close()
