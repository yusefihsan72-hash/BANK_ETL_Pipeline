# validation/report.py
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

def save_quarantine(df: pd.DataFrame, source: str):
    if df.empty:
        return
    path = Path("quarantine") / f"{source}_quarantine.csv"
    path.parent.mkdir(exist_ok=True)
    df["validation_run"] = datetime.utcnow().isoformat()
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False)

def save_summary(passed_count, failed_count, source: str):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summary = {
        "run_timestamp": ts, "source": source,
        "total": passed_count + failed_count,
        "passed": passed_count, "failed": failed_count,
        "quality_pct": round(passed_count / max(passed_count + failed_count, 1) * 100, 2)
    }
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"validation_{source}_{ts}.json").write_text(
        json.dumps(summary, indent=2))
    md = f"""# Validation Report — {source}
**Run:** {ts}

| Metric | Value |
|--------|-------|
| Total records | {summary['total']} |
| Passed | {summary['passed']} |
| Failed | {summary['failed']} |
| Quality % | {summary['quality_pct']}% |
"""
    (out_dir / f"validation_{source}_{ts}.md").write_text(md)