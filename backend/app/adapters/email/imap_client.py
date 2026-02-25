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
                emails.append(
                    {
                        "message_id": msg.get("Message-ID", str(uid)),
                        "subject": msg.get("Subject", ""),
                        "sender": msg.get("From", ""),
                        "body_text": "",
                        "raw": raw,
                    }
                )
        return emails
