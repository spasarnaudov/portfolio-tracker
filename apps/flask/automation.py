from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
AUTO_TAVEX_IMPORT_FLAG = RUNTIME_DIR / "auto_tavex_import.enabled"


def is_auto_tavex_import_enabled():
    return AUTO_TAVEX_IMPORT_FLAG.exists()
