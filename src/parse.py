# src/parse.py
import os
import mailparser
from dateutil import parser as dateparser
from typing import Dict, Generator
from datetime import datetime

def iter_maildir(path: str) -> Generator[Dict, None, None]:
    """Yield parsed mails from a Maildir root (walks recursively)."""
    for root, _, files in os.walk(path):
        for f in files:
            if f.startswith("."): 
                continue
            fp = os.path.join(root, f)
            try:
                m = mailparser.parse_from_file(fp)
            except Exception:
                continue
            try:
                from_addr = m.from_[0][1] if m.from_ else ""
            except Exception:
                from_addr = ""
            body = ""
            if m.text_plain:
                body = "\n\n".join(m.text_plain)
            elif m.body:
                body = m.body
            attachments = []
            try:
                attachments = [att.get("filename", "") for att in m.attachments] if m.attachments else []
            except Exception:
                attachments = []
            raw_date = None
            try:
                raw_date = m.headers.get("date")
            except Exception:
                raw_date = None

            yield {
                "path": fp,
                "subject": m.subject or "",
                "from": from_addr,
                "date": normalize_date(raw_date),
                "body": body,
                "attachments": attachments,
            }
def normalize_date(d):
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    try:
        return dateparser.parse(d)
    except Exception:
        return None

def parse_mail_from_path(path: str) -> Dict:
    """Parse a single mail file path and return dict (same keys as iter_maildir yields)."""
    try:
        m = mailparser.parse_from_file(path)
    except Exception as e:
        raise RuntimeError(f"parse error {path}: {e}")
    try:
        from_addr = m.from_[0][1] if m.from_ else ""
    except Exception:
        from_addr = ""
    body = ""
    if m.text_plain:
        body = "\n\n".join(m.text_plain)
    elif m.body:
        body = m.body
    attachments = []
    try:
        attachments = [att.get("filename", "") for att in m.attachments] if m.attachments else []
    except Exception:
        attachments = []
    return {
        "path": path,
        "subject": m.subject or "",
        "from": from_addr,
        "date": normalize_date(m.date),
        "body": body,
        "attachments": attachments,
    }
