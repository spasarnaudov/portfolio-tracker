# Shared "find a Python >=3.10 interpreter" check. Meant to be sourced, not
# executed directly.
#
# macOS ships an old python3 stub (Xcode Command Line Tools, currently
# 3.9.x) at /usr/bin/python3, which `command -v python3` happily finds —
# but apps/flask/requirements.txt pins packages (e.g. click==8.4.2) that
# require Python >=3.10. A bare existence check would pass on that stub and
# only fail later, confusingly, during `pip install`. So check the version,
# not just presence.
#
# Usage: source "$PROJECT_DIR/scripts/lib/find_python.sh"; find_suitable_python
# Echoes the interpreter's path and returns 0, or returns 1 with nothing
# echoed if none was found.

find_suitable_python() {
    local candidate
    for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" &>/dev/null &&
            "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}
