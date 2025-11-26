# src/main.py
import os
import json
from pathlib import Path
from .pipeline import process_email
from .parse import iter_maildir
import traceback

MAILDIR = os.path.expanduser(os.getenv("SMARTMAIL_MAILDIR", "~/Projects/smart-mail/data/maildir"))
OUT = os.path.expanduser(os.getenv("SMARTMAIL_OUT", "~/.local/share/smartmail/output.json"))
NUM_EMAILS = 5 
def main():
    results = []
    for mail in iter_maildir(MAILDIR):
        # print(f"Processing {mail['path']}...", end="\r")
        path = mail["path"]
        try:
            r = process_email(path)
            results.append(r)
        except Exception as e:
            print(f"error processing {path}: {e}")
            traceback.print_exc()

    results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    top5 = results[:NUM_EMAILS]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(top5, fh, indent=2)
    print(f"Wrote top {len(top5)} to {OUT}")

if __name__ == "__main__":
    main()
