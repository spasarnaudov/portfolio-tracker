#!/usr/bin/env bash

set -Eeuo pipefail

# One-time machine setup for a new Portfolio Tracker server host. Written for
# macOS on Apple Silicon (Homebrew + Docker Desktop) — the alpha/beta/production
# checkouts all share this machine's single PostgreSQL container, per
# scripts/README.md and docs/database-operations.md.
#
# Run this ONCE per machine, before following "Setting Up a New Environment"
# in scripts/README.md for any individual checkout. It is safe to re-run: every
# step first checks whether it's already done.
#
# Prompts interactively for the PostgreSQL superuser password the first time
# the container is created — this script never generates, hardcodes, or
# stores that password itself.

echo "=== Portfolio Tracker server setup ==="
echo

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script is written for macOS. Detected: $(uname -s)."
    echo "It may still mostly work (the Docker/Postgres steps are OS-agnostic),"
    echo "but the Homebrew/Docker Desktop steps below assume macOS."
    read -r -p "Continue anyway? [y/N] " CONTINUE
    [[ "$CONTINUE" =~ ^[Yy]$ ]] || exit 1
fi

# --- Homebrew ---
if ! command -v brew &>/dev/null; then
    echo "Homebrew not found — installing (this will ask for your Mac login password)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [[ -x /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    echo "Homebrew installed. Add this to your shell profile (~/.zprofile) if the"
    echo "installer didn't already:"
    echo '  eval "$(/opt/homebrew/bin/brew shellenv)"'
else
    echo "Homebrew already installed: $(brew --version | head -1)"
fi
echo

# --- git ---
if ! command -v git &>/dev/null; then
    echo "git not found — installing via Homebrew..."
    brew install git
else
    echo "git already installed: $(git --version)"
fi
echo

# --- python3 ---
if ! command -v python3 &>/dev/null; then
    echo "python3 not found — installing via Homebrew..."
    brew install python@3.12
else
    echo "python3 already installed: $(python3 --version)"
fi
echo

# --- Docker Desktop ---
if ! command -v docker &>/dev/null; then
    echo "Docker not found — installing Docker Desktop via Homebrew..."
    brew install --cask docker
    echo
    echo "Launching Docker Desktop for first-time setup..."
    open -a Docker
else
    echo "Docker already installed: $(docker --version)"
    open -a Docker 2>/dev/null || true
fi

# Docker Desktop's own first-launch flow needs someone at the screen for its
# EULA and its privileged-helper install — that install step shows macOS's
# own native authorization dialog (password or Touch ID) and there is no
# legitimate way to script past that boundary, nor should there be. What we
# CAN do is not make the person babysit Terminal too: just poll until the
# daemon responds, so the only thing they actually have to do is answer
# whatever dialog macOS/Docker puts on screen.
echo "Waiting for the Docker daemon to respond (up to 5 minutes — respond to"
echo "any Docker/macOS dialogs that appear, this will continue on its own"
echo "once you do)..."
DOCKER_READY=0
for _ in $(seq 1 150); do
    if docker info &>/dev/null; then
        DOCKER_READY=1
        break
    fi
    sleep 2
done
if [[ "$DOCKER_READY" -ne 1 ]]; then
    echo "ERROR: Docker daemon still not responding after 5 minutes."
    echo "Open Docker Desktop manually, finish any dialogs, wait for the whale"
    echo "icon to stop animating, then re-run this script."
    exit 1
fi
echo "Docker daemon is ready."
echo

echo "Registering Docker Desktop as a login item, so the postgresql container"
echo "(restart policy 'unless-stopped') comes back automatically after a reboot..."
if osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/Docker.app", hidden:false}' &>/dev/null; then
    echo "Done. (If macOS just asked to let Terminal control 'System Events',"
    echo "that's this step — allow it.)"
else
    echo "Could not set this automatically (macOS may have denied Terminal"
    echo "automation permission). Set it by hand instead:"
    echo "  Docker Desktop -> Settings -> General ->"
    echo "  enable 'Start Docker Desktop when you log in'."
fi
echo

# --- Tailscale (expected to already be installed) ---
if ! command -v tailscale &>/dev/null; then
    echo "ERROR: Tailscale not found on PATH, but it's expected to already be"
    echo "installed on this machine. Install it from https://tailscale.com/download,"
    echo "sign in, then re-run this script."
    exit 1
fi
if ! tailscale status &>/dev/null; then
    echo "ERROR: Tailscale is installed but not connected. Run 'tailscale up',"
    echo "sign in, then re-run this script."
    exit 1
fi
echo "Tailscale is connected."
echo "MagicDNS name for this machine (needed for the Android/iOS clients'"
echo "API_BASE_URL, see apps/android/docs/BUILD_VARIANTS.md):"
tailscale status --self 2>/dev/null | head -1
echo

# --- PostgreSQL container ---
POSTGRES_CONTAINER_NAME="postgresql"
POSTGRES_IMAGE="postgres:17.4"

if docker inspect "$POSTGRES_CONTAINER_NAME" &>/dev/null; then
    echo "Container '$POSTGRES_CONTAINER_NAME' already exists."
    if [[ "$(docker inspect --format='{{.State.Running}}' "$POSTGRES_CONTAINER_NAME")" != "true" ]]; then
        echo "Starting it..."
        docker start "$POSTGRES_CONTAINER_NAME"
    fi
    echo "Nothing more to do here — this script does not touch an existing"
    echo "container's data or password."
else
    echo "Creating the '$POSTGRES_CONTAINER_NAME' container ($POSTGRES_IMAGE)."
    echo "This is a NEW machine, so choose a fresh PostgreSQL superuser"
    echo "password now — pick something you'll store in a password manager,"
    echo "not a placeholder you'll forget:"
    read -r -s -p "PostgreSQL superuser (casaos) password: " PG_PASSWORD
    echo
    read -r -s -p "Confirm password: " PG_PASSWORD_CONFIRM
    echo

    if [[ -z "$PG_PASSWORD" ]]; then
        echo "ERROR: password cannot be empty."
        exit 1
    fi
    if [[ "$PG_PASSWORD" != "$PG_PASSWORD_CONFIRM" ]]; then
        echo "ERROR: passwords did not match. Re-run the script."
        exit 1
    fi

    docker volume create postgresql_data >/dev/null

    docker run -d \
        --name "$POSTGRES_CONTAINER_NAME" \
        --restart unless-stopped \
        -e POSTGRES_USER=casaos \
        -e POSTGRES_PASSWORD="$PG_PASSWORD" \
        -p 5432:5432 \
        -v postgresql_data:/var/lib/postgresql/data \
        "$POSTGRES_IMAGE" >/dev/null

    unset PG_PASSWORD PG_PASSWORD_CONFIRM

    echo "Waiting for PostgreSQL to accept connections..."
    READY=0
    for _ in $(seq 1 30); do
        if docker exec "$POSTGRES_CONTAINER_NAME" pg_isready --quiet 2>/dev/null; then
            READY=1
            break
        fi
        sleep 1
    done
    if [[ "$READY" -ne 1 ]]; then
        echo "ERROR: PostgreSQL did not become ready in time."
        echo "Check: docker logs $POSTGRES_CONTAINER_NAME"
        exit 1
    fi

    echo "PostgreSQL is up, container set to restart automatically (unless-stopped)."
    echo
    echo "Save the username/password you just entered now (e.g. in your"
    echo "password manager) — every environment's .env will need it in its"
    echo "DATABASE_URL: postgresql://casaos:<password>@localhost:5432/<db_name>"
fi
echo

echo "=== Server setup complete ==="
echo
echo "Next, for each environment (alpha, beta, production):"
echo "  1. git clone this repo into its own directory"
echo "  2. python3 -m venv apps/flask/.venv && apps/flask/.venv/bin/pip install -r apps/flask/requirements.txt"
echo "  3. ./scripts/init_env.sh   (generates .env interactively — see scripts/README.md)"
echo "  4. docker exec postgresql createdb -U casaos <db_name from step 3>"
echo "  5. ./scripts/init_database.sh"
echo "  6. ./scripts/install_cron.sh"
echo "  7. ./scripts/start_app.sh"
