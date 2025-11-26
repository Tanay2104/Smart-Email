# CLeanup file
import time
import email
import os
from email.parser import BytesParser
from email.utils import parsedate_to_datetime

# --- Configuration ---
MAIL_ROOT = os.path.expanduser("~/Projects/smart-mail/data/maildir")
DAYS_TO_KEEP = 20
DRY_RUN = False # Be careful!

def get_email_date(filepath):
    """Reads the email file and returns its Date header as a timestamp."""
    try:
        with open(filepath, 'rb') as f:
            # We only need the headers, so stop after headers
            parser = BytesParser()
            headers = parser.parse(f, headersonly=True)
            
            date_str = headers['Date']
            if not date_str:
                return os.path.getmtime(filepath) # Fallback
            
            # Parse date string to datetime object
            email_date = parsedate_to_datetime(date_str)
            return email_date.timestamp()
    except Exception as e:
        # If we can't read it, assume it's new to be safe
        return time.time() 

cutoff_time = time.time() - (DAYS_TO_KEEP * 86400)

def clean_folder(folder_path):
    deleted = 0
    for root, dirs, files in os.walk(folder_path):
        if os.path.basename(root) in ['cur', 'new']:
            for file in files:
                filepath = os.path.join(root, file)
                
                # Get true date from email header
                email_ts = get_email_date(filepath)
                
                if email_ts < cutoff_time:
                    if DRY_RUN:
                        print(f"[DRY RUN] Old email found: {filepath}")
                    else:
                        try:
                            os.remove(filepath)
                            deleted += 1
                            # print(f"Deleted: {file}") # Uncomment for verbose
                        except OSError:
                            pass
    return deleted

print(f"Cleaning emails older than {DAYS_TO_KEEP} days...")
for account in ["iitb", "gmail"]:
    path = os.path.join(MAIL_ROOT, account)
    if os.path.exists(path):
        count = clean_folder(path)
        print(f"[{account}] Deleted {count} emails.")
