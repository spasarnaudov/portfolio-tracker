# Shared Docker/PostgreSQL preflight check. Meant to be sourced, not executed
# directly, by scripts that talk to PostgreSQL through the Docker container
# instead of a locally installed pg_dump/pg_restore/psql.
#
# Usage: source "$PROJECT_DIR/scripts/lib/docker_postgres.sh"; require_postgres_container

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgresql}"

require_postgres_container() {
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker is not installed or not on PATH."
        exit 1
    fi

    if ! docker inspect "$POSTGRES_CONTAINER_NAME" &> /dev/null; then
        echo "ERROR: No Docker container named '$POSTGRES_CONTAINER_NAME' was found."
        echo "Set POSTGRES_CONTAINER_NAME in .env if the container has a different name."
        exit 1
    fi

    if [[ "$(docker inspect --format='{{.State.Running}}' "$POSTGRES_CONTAINER_NAME")" != "true" ]]; then
        echo "ERROR: Container '$POSTGRES_CONTAINER_NAME' exists but is not running."
        echo "Start it with: docker start $POSTGRES_CONTAINER_NAME"
        exit 1
    fi

    if ! docker exec "$POSTGRES_CONTAINER_NAME" pg_isready --quiet; then
        echo "ERROR: PostgreSQL inside container '$POSTGRES_CONTAINER_NAME' is not accepting connections."
        exit 1
    fi
}
