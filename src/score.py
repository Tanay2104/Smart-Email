import json
import re
from typing import Dict, Any, Optional
from .llama import call_llama

PROMPT_TEMPLATE = """You are a smart executive assistant. 
Your Goal: Identify important emails and ignore spam/noise.

RULES for Importance Scoring:
1.  **College/Clubs:** If the email is from a college tech team, student club, hackathon, or mass promotional recruitment, mark importance < 20 and task as "Archive".
2.  **Real Offers:** Only mark "Internship/Job" as HIGH importance (> 80) if it is a direct interview invite or an official offer letter addressed specifically to me.
3.  **General:** Promotional emails, newsletters, and automated notifications should be importance < 10.

Output ONLY valid JSON with these keys:
{{"importance": <number 0-100>, "task": "<one-line actionable task>", "reason": "<short reason>", "due": "<YYYY-MM-DD or null>"}}

Email Subject:
{subject}

Email Body:
{body}

Context: Domain: {domain}; From: {from_header}
"""

def _extract_last_json(s: str) -> Optional[Dict[str, Any]]:
    # fallback: simple conservative json extractor
    braces = []
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if start is None:
                start = i
            braces.append(i)
        elif ch == "}":
            if braces:
                braces.pop()
                if not braces and start is not None:
                    candidate = s[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # continue scanning
                        start = None
                        braces = []
    return None

def safe_extract_json(s: str) -> Optional[Dict[str, Any]]:
    # first try simple find
    try:
        m = re.findall(r"\{.*\}", s, re.S)
        if m:
            return json.loads(m[-1])
    except Exception:
        pass
    return _extract_last_json(s)

def score_email(subject: str, body: str, domain: str, from_header: str) -> Dict:
    # FIX: Truncate body to prevent exceeding context limits (approx 2000 chars)
    trunc_body = body[:2000] if body else ""
    trunc_subject = subject[:200] if subject else ""
    
    prompt = PROMPT_TEMPLATE.format(subject=trunc_subject, body=trunc_body, domain=domain, from_header=from_header)
    
    try:
        # Increased timeout slightly for safety
        out = call_llama(prompt, max_tokens=256, temperature=0.0, timeout=45)
    except Exception as e:
        return {"importance": 10.0, "task": "", "reason": f"LLM failure: {e}", "due": None}
    
    parsed = safe_extract_json(out)
    if parsed is None:
        # Return default if parsing fails
        return {"importance": 10.0, "task": "", "reason": "LLM produced unparsable output", "due": None}
        
    importance = parsed.get("importance", 10)
    try:
        importance = float(importance)
        importance = max(0.0, min(100.0, importance))
    except Exception:
        importance = 10.0
        
    return {
        "importance": importance,
        "task": parsed.get("task", "")[:512],
        "reason": parsed.get("reason", "")[:512],
        "due": parsed.get("due", None)
    }
