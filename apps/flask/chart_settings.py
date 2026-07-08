import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
CHART_FILTERS_PATH = RUNTIME_DIR / "chart_filters.json"

DEFAULT_CHART_FILTERS = {
    "asset_id": None,
    "range": "1d",
    "interval": "recorded",
    "start_date": None,
    "end_date": None,
}


def load_chart_filters():
    if not CHART_FILTERS_PATH.exists():
        return DEFAULT_CHART_FILTERS.copy()

    try:
        saved_filters = json.loads(CHART_FILTERS_PATH.read_text())
    except json.JSONDecodeError:
        return DEFAULT_CHART_FILTERS.copy()

    chart_filters = DEFAULT_CHART_FILTERS.copy()
    chart_filters.update({
        key: saved_filters.get(key)
        for key in DEFAULT_CHART_FILTERS
    })

    return chart_filters


def save_chart_filters(chart_filters):
    RUNTIME_DIR.mkdir(exist_ok=True)
    CHART_FILTERS_PATH.write_text(json.dumps(chart_filters, indent=2))
