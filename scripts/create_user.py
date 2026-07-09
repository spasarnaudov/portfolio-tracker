import argparse
import getpass
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_PATH = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_PATH))

from repository import save_user  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update an application user.")
    parser.add_argument("username", help="Username used for login.")
    parser.add_argument(
        "--password",
        help="Password for the user. If omitted, you will be prompted.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    username = args.username.strip()

    if not username:
        raise SystemExit("Username cannot be empty.")

    password = args.password or getpass.getpass("Password: ")

    if not password:
        raise SystemExit("Password cannot be empty.")

    user = save_user(username, generate_password_hash(password))
    print(f"Saved user: {user['username']}")


if __name__ == "__main__":
    main()
