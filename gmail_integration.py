import email
import imaplib
import os
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from db import DB_NAME, get_connection, init_db
from models import create_email_log


GMAIL_IMAP_HOST = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
HR_SUBJECT_KEYWORDS = ("interview", "discussion", "hr", "hiring", "schedule")
JOB_BOARD_DOMAINS = ("naukri.com",)


def _decode_mime_header(value: str | None) -> str:
    if not value:
        return ""

    decoded_parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts).strip()


def _message_datetime(message: Message) -> str | None:
    date_header = message.get("Date")
    if not date_header:
        return None

    try:
        return parsedate_to_datetime(date_header).isoformat()
    except (TypeError, ValueError, IndexError):
        return date_header


def _text_from_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _snippet_from_message(message: Message, max_length: int = 240) -> str:
    text = ""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                text = _text_from_part(part)
                break
    elif message.get_content_type() == "text/plain":
        text = _text_from_part(message)

    return " ".join(text.split())[:max_length]


def _matches_hr_filter(subject: str, sender: str) -> bool:
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    return any(keyword in subject_lower for keyword in HR_SUBJECT_KEYWORDS) or any(
        domain in sender_lower for domain in JOB_BOARD_DOMAINS
    )


def _imap_credentials() -> tuple[str, str]:
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Gmail is not configured yet. Set GMAIL_USERNAME and GMAIL_APP_PASSWORD, then try again."
        )
    return username, password


def fetch_recent_hr_emails(max_count: int = 50) -> list[dict[str, Any]]:
    username, password = _imap_credentials()
    emails: list[dict[str, Any]] = []

    with imaplib.IMAP4_SSL(GMAIL_IMAP_HOST, GMAIL_IMAP_PORT) as mail:
        mail.login(username, password)
        mail.select("INBOX", readonly=True)

        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return emails

        message_numbers = data[0].split()
        for message_number in reversed(message_numbers):
            if len(emails) >= max_count:
                break

            status, fetched = mail.fetch(message_number, "(BODY.PEEK[])")
            if status != "OK" or not fetched:
                continue

            raw_message = fetched[0][1]
            if not isinstance(raw_message, bytes):
                continue

            message = email.message_from_bytes(raw_message)
            subject = _decode_mime_header(message.get("Subject"))
            sender = _decode_mime_header(message.get("From"))
            if not _matches_hr_filter(subject, sender):
                continue

            emails.append(
                {
                    "provider": "Gmail",
                    "message_id": (message.get("Message-ID") or "").strip(),
                    "subject": subject,
                    "sender": sender,
                    "received_at": _message_datetime(message),
                    "snippet": _snippet_from_message(message),
                }
            )

    return emails


def store_email_logs(emails: list[dict[str, Any]], db_path: str | Path = DB_NAME) -> int:
    init_db(db_path)
    inserted_count = 0

    conn = get_connection(db_path)
    try:
        existing_message_ids = {
            row["message_id"]
            for row in conn.execute(
                "SELECT message_id FROM email_logs WHERE provider = ? AND message_id IS NOT NULL",
                ("Gmail",),
            ).fetchall()
        }
    finally:
        conn.close()

    for email_data in emails:
        message_id = email_data.get("message_id")
        if message_id and message_id in existing_message_ids:
            continue

        create_email_log(
            provider=email_data.get("provider", "Gmail"),
            message_id=message_id,
            subject=email_data.get("subject"),
            sender=email_data.get("sender"),
            received_at=email_data.get("received_at"),
            snippet=email_data.get("snippet"),
            db_path=db_path,
        )
        inserted_count += 1
        if message_id:
            existing_message_ids.add(message_id)

    return inserted_count
