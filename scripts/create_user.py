import argparse
import getpass
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLASK_APP_PATH = PROJECT_ROOT / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_PATH))

from repository import save_user  # noqa: E402


VALID_ROLES = {"admin", "user", "demo"}


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update an application user.")
    parser.add_argument("username", help="Username used for login.")
    parser.add_argument(
        "--password",
        help="Password for the user. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--role",
        choices=sorted(VALID_ROLES),
        default="user",
        help="Application role for the user.",
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

    user = save_user(username, generate_password_hash(password), args.role)
    print(f"Saved user: {user['username']} ({user['role']})")


if __name__ == "__main__":
    main()
