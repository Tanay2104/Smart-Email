# src/pipeline.py
from .parse import parse_mail_from_path
from .faiss_helper import FaissHelper
from .embed import embed_text
from .score import score_email
from .classify import rule_score
import math

faiss_helper = FaissHelper()


def process_email(path: str) -> dict:
    mail = parse_mail_from_path(path)
    text = (mail.get("subject") or "") + "\n\n" + (mail.get("body") or "")
    emb = embed_text(text)
    domains = faiss_helper.query(emb, k=3)
    domain = domains[0]["name"] if domains else "unknown"

    rscore = rule_score(mail)  # returns 0.0-1.0
    if rscore > 0.3:
        llm_out = score_email(
            mail.get("subject", ""), mail.get("body", ""), domain, mail.get("from", "")
        )
        llm_score = llm_out.get("importance", 10.0)
    else:
        llm_score = 0.0
        llm_out = {}

    combined = 0.7 * (rscore * 100.0) + 0.3 * llm_score
    combined = float(combined)

    return {
        "path": path,
        "subject": mail.get("subject", ""),
        "from": mail.get("from", ""),
        "date": str(mail.get("date", "")),
        "domain": domain,
        "domain_candidates": domains,
        "rule_score": rscore,
        "llm_score": llm_score,
        "combined_score": combined,
        "task": llm_out.get("task", ""),
        "reason": llm_out.get("reason", ""),
        "due": llm_out.get("due", None),
    }
