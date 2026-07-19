"""TalentUP Fichaje — Run Alembic migrations.

Usage:
    python run_migrations.py          # upgrade to latest
    python run_migrations.py downgrade  # downgrade one step
    python run_migrations.py <target>   # migrate to specific revision
"""
import os
import sys
import subprocess


def main():
    """Run Alembic migrations from the backend directory."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # Determine the command: upgrade (default) or downgrade
    args = sys.argv[1:] if len(sys.argv) > 1 else ["upgrade", "head"]

    cmd = [sys.executable, "-m", "alembic"] + args

    print(f"🔧 Running: {' '.join(cmd)}")
    print(f"   CWD: {backend_dir}")
    print()

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n❌ Migration failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print("\n✅ Migrations applied successfully.")


if __name__ == "__main__":
    main()
