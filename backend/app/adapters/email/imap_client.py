from email import message_from_bytes
from typing import Any

from imapclient import IMAPClient

from backend.app.utils.crypto import decrypt_secret


class ImapClientAdapter:
    def __init__(self, host: str, port: int, username: str, password_enc: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = decrypt_secret(password_enc)
        self.use_ssl = use_ssl

    def test_connection(self) -> bool:
        with IMAPClient(self.host, port=self.port, ssl=self.use_ssl) as client:
            client.login(self.username, self.password)
            return True

    def fetch_recent(self, folder: str = "INBOX", limit: int = 20) -> list[dict[str, Any]]:
        emails: list[dict[str, Any]] = []
        with IMAPClient(self.host, port=self.port, ssl=self.use_ssl) as client:
            client.login(self.username, self.password)
            client.select_folder(folder)
            messages = client.search(["ALL"])
            for uid, data in client.fetch(messages[-limit:], [b"RFC822"]).items():
                raw = data[b"RFC822"]
                msg = message_from_bytes(raw)
                body_text = self._extract_body_text(msg)
                attachments = self._extract_attachments(msg)
                emails.append(
                    {
                        "message_id": msg.get("Message-ID", str(uid)),
                        "subject": msg.get("Subject", ""),
                        "sender": msg.get("From", ""),
                        "body_text": body_text,
                        "attachments": attachments,
                        "raw": raw,
                    }
                )
        return emails

    def _extract_body_text(self, msg) -> str:
        if msg.is_multipart():
            parts: list[str] = []
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition.lower():
                    continue
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    parts.append(payload.decode(charset, errors="ignore"))
            return "\n".join(parts).strip()

        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="ignore").strip()

    def _extract_attachments(self, msg) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if not msg.is_multipart():
            return items

        for part in msg.walk():
            filename = part.get_filename()
            if not filename:
                continue
            content = part.get_payload(decode=True) or b""
            if not content:
                continue
            items.append(
                {
                    "filename": filename,
                    "mime_type": part.get_content_type(),
                    "content": content,
                }
            )
        return items
