import yaml
import re
import os
from datetime import datetime, timezone


def rule_score(email):
    # Assigns weights to emails based on predecided values.
    domains = []
    # Safely try to load the config, fallback to empty if missing
    if os.path.exists("config/domains.yml"):
        try:
            with open("config/domains.yml") as f:
                data = yaml.safe_load(f)
                if data:
                    domains = data.get("important_domains", [])
        except Exception as e:
            print(f"Warning: could not load domains: {e}")

    s = 0.0

    # Domain score
    # Safe extraction of domain
    from_addr = email.get("from", "")
    if from_addr:
        try:
            domain = from_addr.split("@")[-1]
            if domain in domains:
                s += 0.4
        except IndexError:
            pass

    # Keyword score
    keywords = [
        "deadline",
        "submit",
        "submission",
        "assigment",
        "assignment",
        "offer",
        "interview",
        "urgent",
        "slot",
        "due soon",
    ]

    # FIX 1: Use correct key 'subject' (singular) and handle None
    subject = email.get("subject") or ""
    body = email.get("body") or ""
    text = f"{subject} {body}".lower()

    for kw in keywords:
        if kw in text:
            s += 0.15

    # Attachment score
    # FIX 2: Use .get() to avoid KeyError if key is missing
    for att in email.get("attachments", []):
        if att.endswith(".pdf"):
            s += 0.1

    # Recency score
    # FIX 3: Correct date math. (datetime - datetime) = timedelta
    date_obj = email.get("date")
    if date_obj and isinstance(date_obj, datetime):
        now = datetime.now(timezone.utc)
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=timezone.utc)
        delta = now - date_obj
        if delta.days <= 2:
            s += 0.2

    return min(s, 1.0)
