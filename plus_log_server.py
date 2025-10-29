import os
import threading
import time
from typing import List, Dict, Any

from flask import Flask, jsonify, render_template

from plus_log_parser import parse_plus_log


LOG_PATH = os.environ.get("PLUS_LOG_PATH", os.path.join(os.getcwd(), "plus.out.log"))
SCAN_INTERVAL_SEC = int(os.environ.get("PLUS_LOG_SCAN_INTERVAL", "60"))


app = Flask(__name__)

_records: List[Dict[str, Any]] = []
_last_read_err: str | None = None


def _read_file_text(path: str) -> str:
    # Try utf-8, fallback to utf-8-sig, gbk
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                return f.read()
        except FileNotFoundError:
            raise
        except Exception:
            continue
    # Last resort
    with open(path, "r", errors="ignore") as f:
        return f.read()


def scan_once():
    global _records, _last_read_err
    try:
        text = _read_file_text(LOG_PATH)
        recs = parse_plus_log(text)
        _records = recs
        _last_read_err = None
    except FileNotFoundError:
        _records = []
        _last_read_err = f"Log file not found: {LOG_PATH}"
    except Exception as e:
        _last_read_err = f"Error parsing log: {e}"


def scanner_loop():
    # Initial delay small to load quickly
    time.sleep(0.5)
    while True:
        scan_once()
        time.sleep(SCAN_INTERVAL_SEC)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/records")
def api_records():
    return jsonify({
        "records": _records,
        "log_path": LOG_PATH,
        "last_error": _last_read_err,
        "count": len(_records),
    })


@app.route("/healthz")
def healthz():
    return ("ok", 200)


def run():
    t = threading.Thread(target=scanner_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)


if __name__ == "__main__":
    run()

