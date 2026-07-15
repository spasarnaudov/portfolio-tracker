import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
CHART_FILTERS_PATH = RUNTIME_DIR / "chart_filters.json"

DEFAULT_CHART_FILTERS = {
    "charts": [],
    "asset_ids": [],
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
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CHART_FILTERS.copy()

    chart_filters = DEFAULT_CHART_FILTERS.copy()
    chart_filters.update({
        key: saved_filters.get(key)
        for key in DEFAULT_CHART_FILTERS
    })

    if not chart_filters["asset_ids"] and saved_filters.get("asset_id"):
        chart_filters["asset_ids"] = [saved_filters["asset_id"]]

    if not chart_filters["charts"] and chart_filters["asset_ids"]:
        chart_filters["charts"] = [
            {
                "asset_id": asset_id,
                "range": chart_filters["range"],
                "interval": chart_filters["interval"],
                "start_date": chart_filters["start_date"],
                "end_date": chart_filters["end_date"],
            }
            for asset_id in chart_filters["asset_ids"]
        ]

    return chart_filters


def save_chart_filters(chart_filters):
    RUNTIME_DIR.mkdir(exist_ok=True)
    CHART_FILTERS_PATH.write_text(json.dumps(chart_filters, indent=2))
