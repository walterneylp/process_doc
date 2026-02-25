from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.app.api.v1.deps import DbDep, get_current_user
from backend.app.db import models
from backend.app.engines.extractor.engine import ExtractionEngine
from backend.app.engines.llm_classifier.engine import LLMClassifierEngine
from backend.app.engines.rules_engine.engine import RulesEngine
from backend.app.engines.validator.engine import ValidatorEngine
from backend.app.utils.document_text import extract_text_from_file
from backend.app.utils.file_types import infer_doc_type
from backend.app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = db.query(models.Document).filter(models.Document.tenant_id == current_user.tenant_id).all()
    return [
        {
            "id": str(i.id),
            "doc_type": i.doc_type,
            "status": i.status,
            "needs_review": i.needs_review,
            "trace_id": i.trace_id,
        }
        for i in items
    ]


@router.get("/review")
def list_review(db: DbDep, current_user: Annotated[models.User, Depends(get_current_user)]):
    items = (
        db.query(models.Document)
        .filter(models.Document.tenant_id == current_user.tenant_id, models.Document.needs_review == True)
        .all()
    )
    return [{"id": str(i.id), "status": i.status} for i in items]


@router.post("/{document_id}/process")
def run_document(document_id: str):
    process_document.delay(document_id)
    return {"status": "QUEUED"}


@router.post("/test-analyze")
async def test_analyze_document(
    db: DbDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    file: UploadFile = File(...),
    subject: str = Form(default=""),
    sender: str = Form(default=""),
    body_text: str = Form(default=""),
):
    suffix = Path(file.filename or "upload.bin").suffix or ".bin"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        extracted_text = extract_text_from_file(tmp_path, file.content_type)
        analysis_parts = [
            f"Assunto: {subject}",
            f"Remetente: {sender}",
            f"Corpo: {body_text}",
            f"Texto do anexo: {extracted_text}",
        ]
        analysis_content = "\n\n".join([p for p in analysis_parts if p.strip()])

        rules_engine = RulesEngine()
        llm_engine = LLMClassifierEngine()
        extraction_engine = ExtractionEngine()
        validator = ValidatorEngine()

        rr = rules_engine.classify(sender, subject, file.filename or "")
        if rr.confidence >= 0.85:
            classification = {
                "category": rr.category,
                "department": rr.department,
                "confidence": rr.confidence,
                "priority": rr.priority,
                "reason": rr.reason,
                "source": "rules",
            }
        else:
            try:
                payload = llm_engine.classify(subject, sender, analysis_content)
                classification = {**payload, "source": "llm"}
            except Exception as exc:
                classification = {
                    "category": "generic",
                    "department": "triage",
                    "confidence": 0.5,
                    "priority": "normal",
                    "reason": f"llm_error:{exc}",
                    "source": "fallback",
                }

        doc_type = infer_doc_type(file.filename or "upload.bin")
        extraction_errors: list[str] = []
        try:
            extraction = extraction_engine.extract(db, current_user.tenant_id, doc_type, analysis_content)
        except Exception as exc:
            extraction = {}
            extraction_errors.append(f"extraction_error:{exc}")

        valid, errors = validator.validate(extraction)
        errors.extend(extraction_errors)
        if extraction_errors:
            valid = False
        if float(classification.get("confidence", 0)) < 0.75 and "low_confidence" not in errors:
            errors.append("low_confidence")
            valid = False

        return {
            "filename": file.filename,
            "doc_type": doc_type,
            "text_preview": extracted_text[:1200],
            "classification": classification,
            "extraction": extraction,
            "valid": valid,
            "errors": errors,
            "needs_review": not valid,
        }
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
