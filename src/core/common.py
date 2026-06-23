
import os
from datetime import datetime
from conf import BOT_LOG_FILE

class SkipJobException(Exception):
    """Raised when the job should be skipped"""
    pass

def log(icon: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {icon}  {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(BOT_LOG_FILE), exist_ok=True)
        with open(BOT_LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass
