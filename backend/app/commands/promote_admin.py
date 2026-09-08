import argparse

from backend.app.admin import UserNotFoundError, promote_user_to_admin
from backend.app.database import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote an existing Reservoir user to admin."
    )
    parser.add_argument("email", help="Email address of the registered user")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with SessionLocal() as database:
        try:
            user = promote_user_to_admin(database, args.email)
        except UserNotFoundError:
            raise SystemExit(f"No registered user found for {args.email}") from None

    print(f"{user.email} is now an admin.")


if __name__ == "__main__":
    main()
