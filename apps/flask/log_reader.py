from collections import deque
from datetime import datetime
from pathlib import Path


LOG_MAX_LINES = 500


def _read_log_tail(log_path: Path, max_lines: int) -> tuple[str, int, int]:
    tail = deque(maxlen=max_lines)
    total_lines = 0

    with log_path.open("rb") as log_file:
        for raw_line in log_file:
            total_lines += 1
            tail.append(raw_line.decode("utf-8", errors="replace"))

    return "".join(tail), len(tail), total_lines


def get_log_files(log_directory: Path, max_lines: int = LOG_MAX_LINES) -> list[dict]:
    if max_lines < 1:
        raise ValueError("max_lines must be greater than zero")

    try:
        if not log_directory.is_dir():
            return []

        directory_path = log_directory.resolve()
        entries = sorted(log_directory.iterdir(), key=lambda path: path.name.lower())
    except (OSError, PermissionError):
        return []

    log_files = []

    for log_path in entries:
        try:
            if log_path.suffix.lower() != ".log" or log_path.is_symlink() or not log_path.is_file():
                continue

            resolved_path = log_path.resolve(strict=True)
            if resolved_path.parent != directory_path:
                continue

            modified_at = datetime.fromtimestamp(resolved_path.stat().st_mtime)
            content, displayed_lines, total_lines = _read_log_tail(resolved_path, max_lines)
            error = None
        except (OSError, PermissionError):
            modified_at = None
            content = ""
            displayed_lines = 0
            total_lines = 0
            error = "Unable to read this log file."

        log_files.append({
            "name": log_path.name,
            "label": log_path.stem.replace("_", " ").capitalize(),
            "content": content,
            "modified_at": modified_at,
            "displayed_lines": displayed_lines,
            "total_lines": total_lines,
            "error": error,
        })

    return log_files
