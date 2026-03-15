# extraction/processed_tracker.py
from pathlib import Path
from datetime import datetime
import json, hashlib

TRACKER_PATH = Path("data/processed/processed_files.json")

def _load():
    return json.loads(TRACKER_PATH.read_text()) if TRACKER_PATH.exists() else {}

def _save(data):
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(data, indent=2))

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def is_processed(path: Path) -> bool:
    return str(path.resolve()) in _load()

def mark_processed(path: Path, hash_val: str):
    data = _load()
    data[str(path.resolve())] = {
        "hash": hash_val,
        "processed_at": datetime.utcnow().isoformat()
    }
    _save(data)