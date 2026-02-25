from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.utils.crypto import sha256_bytes


class LocalStorageAdapter:
    def __init__(self) -> None:
        self.root = Path(get_settings().storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_attachment(self, tenant_id: str, email_id: str, filename: str, content: bytes) -> tuple[str, str]:
        folder = self.root / tenant_id / email_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_bytes(content)
        return str(path), sha256_bytes(content)
