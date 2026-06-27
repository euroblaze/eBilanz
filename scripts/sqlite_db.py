#!/usr/bin/env python3
"""SQLite-Wartung: init | backup | restore.

Wiederverwendet die Backend-Modelle (keine Duplizierung). Backups liegen in
data/sqlite_backups/ (globale Konvention).

Aufruf (aus Repo-Root, venv aktiv):
  python scripts/sqlite_db.py init
  python scripts/sqlite_db.py backup
  python scripts/sqlite_db.py restore data/sqlite_backups/ebilanz_<ts>.sqlite
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Backend importierbar machen (backend/ auf sys.path).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import ROOT_DIR, settings  # noqa: E402
from app.seed import init_db  # noqa: E402

BACKUP_DIR = ROOT_DIR / "data" / "sqlite_backups"


def cmd_init() -> None:
    init_db()
    db = settings.db_file
    if db.exists():
        db.chmod(0o600)  # minimale Rechte
    print(f"OK init: {db}")


def cmd_backup() -> None:
    db = settings.db_file
    if not db.exists():
        sys.exit(f"Keine DB gefunden: {db} (zuerst 'init').")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    target = BACKUP_DIR / f"ebilanz_{ts}.sqlite"
    shutil.copy2(db, target)
    target.chmod(0o600)
    print(f"OK backup: {target}")


def cmd_restore(arg: str) -> None:
    src = Path(arg)
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        sys.exit(f"Backup nicht gefunden: {src}")
    db = settings.db_file
    db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, db)
    db.chmod(0o600)
    print(f"OK restore: {src} -> {db}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Befehl fehlt: init | backup | restore <datei>")
    cmd = sys.argv[1]
    if cmd == "init":
        cmd_init()
    elif cmd == "backup":
        cmd_backup()
    elif cmd == "restore":
        if len(sys.argv) < 3:
            sys.exit("restore benötigt eine Backup-Datei.")
        cmd_restore(sys.argv[2])
    else:
        sys.exit(f"Unbekannter Befehl: {cmd}")


if __name__ == "__main__":
    main()
