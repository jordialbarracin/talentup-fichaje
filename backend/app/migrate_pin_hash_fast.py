"""
Migration script: backfill pin_hash_fast for existing employees.

Usage:
    cd /d/talentup-fichaje/backend
    python -m app.migrate_pin_hash_fast
"""
import asyncio
import os
import sys

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SQLITE_FALLBACK"] = "true"

from sqlalchemy import select
from app.database import async_session_factory, init_db
from app.models.employee import Employee
from app.auth import compute_pin_hash_fast, verify_password


async def migrate():
    print("🔧 Migrating existing employees: backfilling pin_hash_fast...")
    await init_db()

    async with async_session_factory() as db:
        result = await db.execute(select(Employee))
        employees = result.scalars().all()

        updated = 0
        skipped = 0
        errors = 0

        for emp in employees:
            if emp.pin_hash_fast:
                skipped += 1
                continue

            # We need the original PIN to compute pin_hash_fast, but we only have
            # the bcrypt hash. We can't reverse it. So we set pin_hash_fast to
            # a placeholder that will never match — the employee must set a new PIN.
            #
            # However, if the employee has a known PIN from seed data, we could
            # compute it. For production, the admin should reset each employee's PIN.
            #
            # For this migration, we'll try to match known PINs from seed data
            # by attempting common PINs (this is a dev/seed scenario).
            # In production, employees would need to reset their PIN via the app.

            # Try common test PINs
            common_pins = ["1234", "5678", "9012", "3456", "7890", "2345", "6789", "0123", "4567", "8901"]
            found = False
            for pin in common_pins:
                if verify_password(pin, emp.pin_hash):
                    emp.pin_hash_fast = compute_pin_hash_fast(pin)
                    found = True
                    updated += 1
                    break

            if not found:
                # For employees whose PIN we can't guess, we set a null placeholder.
                # The employee will need to reset their PIN.
                # We set it to an impossible hash so the employee can't clock in
                # until they reset their PIN.
                print(f"  ⚠️  {emp.name} ({emp.id}): PIN not guessable. Set to null placeholder.")
                # Set to a value that will never match any PIN
                emp.pin_hash_fast = "MIGRATION_PENDING_" + emp.id[:8]
                errors += 1

        await db.commit()

    print(f"\n✅ Migration complete: {updated} updated, {skipped} already set, {errors} with unknown PINs")
    print("ℹ️  Employees with unknown PINs need their PIN reset via the admin panel.")


if __name__ == "__main__":
    asyncio.run(migrate())
