"""Create a staff account (LOGISTICS_MANAGER or ADMIN) for a phone number.

Public sign-up only allows FARMER, BUYER, VENDOR (and DELIVERY_AGENT for drivers), so staff
accounts are made here, by hand, by Atharv. Run it from the backend/ folder:

    python scripts/create_staff_user.py 9876543210
    python scripts/create_staff_user.py 9876543210 --role ADMIN

It uses DATABASE_URL from backend/.env (or the environment), so with the production URL it creates
the account in the LIVE database. It asks you to type "yes" first (skip with --yes). It only ever
ADDS a new user: if the phone number already has an account it stops and changes nothing.
Afterwards the person logs in with the normal phone + OTP login.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()  # before any app import: settings read the environment

STAFF_ROLES = ("LOGISTICS_MANAGER", "ADMIN")  # never SUPER_ADMIN, never a public sign-up role


async def create_staff_user(phone_number: str, role_name: str) -> str:
    """Add the user and return a one-line result. Never touches an existing user."""
    import app.domain_model_registry  # noqa: F401  (registers every model)
    import app.models.address  # noqa: F401  (User points at Address; the app loads it via the routers)
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal, close_database
    from app.core.enums import AccountStatus
    from app.models.role import Role
    from app.models.user import User
    from app.schemas.auth.otp import normalize_indian_phone

    phone = normalize_indian_phone(phone_number)
    try:
        async with AsyncSessionLocal() as session:
            role = await session.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                return f"Stopped: role {role_name} does not exist in this database (start the backend once first)."
            if await session.scalar(select(User.id).where(User.phone_number == phone)):
                return f"Stopped: {phone} already has an account. Nothing was changed."
            session.add(
                User(
                    public_id=uuid4(),
                    phone_number=phone,
                    role_id=role.id,
                    phone_verified_at=datetime.now(timezone.utc),
                    account_status=AccountStatus.ACTIVE,
                )
            )
            await session.commit()
        return f"Done: {phone} is now a {role_name}. They can log in with phone + OTP."
    finally:
        await close_database()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a LOGISTICS_MANAGER or ADMIN account.")
    parser.add_argument("phone", help="Indian mobile number, e.g. 9876543210 or +919876543210")
    parser.add_argument("--role", default="LOGISTICS_MANAGER", choices=STAFF_ROLES)
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    args = parser.parse_args()

    from app.schemas.auth.otp import normalize_indian_phone

    try:
        phone = normalize_indian_phone(args.phone)
    except ValueError as exc:
        print(f"Stopped: {exc}")
        return 1

    if not args.yes:
        answer = input(f"Create {args.role} {phone} in the database from DATABASE_URL? Type yes: ")
        if answer.strip().lower() != "yes":
            print("Cancelled. Nothing was changed.")
            return 1

    print(asyncio.run(create_staff_user(phone, args.role)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
