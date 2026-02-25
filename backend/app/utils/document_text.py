import subprocess
from pathlib import Path
from shutil import which


TEXT_SUFFIXES = {".txt", ".csv", ".json", ".xml", ".md", ".log"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def _safe_trim(text: str, max_chars: int) -> str:
    return text[:max_chars].strip() if text else ""


def _extract_pdf_text(path: Path) -> str:
    if which("pdftotext"):
        try:
            result = subprocess.run(
                ["pdftotext", str(path), "-"],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            pass

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def _extract_image_text(path: Path) -> str:
    if not which("tesseract"):
        return ""
    try:
        result = subprocess.run(
            ["tesseract", str(path), "stdout"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        if result.returncode == 0:
            return result.stdout or ""
    except Exception:
        return ""
    return ""


def extract_text_from_file(file_path: str, mime_type: str | None = None, max_chars: int = 20000) -> str:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return ""

    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        try:
            return _safe_trim(path.read_text(encoding="utf-8", errors="ignore"), max_chars)
        except Exception:
            return ""

    if suffix == ".pdf" or (mime_type and "pdf" in mime_type.lower()):
        return _safe_trim(_extract_pdf_text(path), max_chars)

    if suffix in IMAGE_SUFFIXES or (mime_type and mime_type.lower().startswith("image/")):
        return _safe_trim(_extract_image_text(path), max_chars)

    try:
        raw = path.read_bytes()[:200000]
        return _safe_trim(raw.decode("utf-8", errors="ignore"), max_chars)
    except Exception:
        return ""
