"""Run from the project root: .venv/Scripts/python.exe scripts/start-integrated.py."""

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5174"))
    os.environ.setdefault(
        "APP_ORIGIN", f"http://localhost:{port},http://127.0.0.1:{port}"
    )
    print(f"Luigi's integrated application: http://localhost:{port}", flush=True)
    uvicorn.run("integrated_app:app", host="127.0.0.1", port=port)
