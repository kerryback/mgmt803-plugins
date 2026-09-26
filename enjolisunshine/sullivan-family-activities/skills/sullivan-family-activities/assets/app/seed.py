"""First-run setup: the family and a starter prize shop. No sample activities."""
from pathlib import Path

from . import services as svc
from .schemas import MemberIn

FAMILY = [
    ("Mom", "parent", "pink"),
    ("Dad", "parent", "blue"),
    ("Matty", "kid", "green"),
    ("Nolie", "kid", "yellow"),
    ("Baby", "kid", "purple"),
]

STARTER_PRIZES = [
    ("🌙", "Stay up 15 minutes later", 6),
    ("🎬", "Pick the family movie", 8),
    ("📺", "30 minutes extra screen time", 10),
    ("🛝", "Trip to the park", 10),
    ("🍕", "Pick what's for dinner", 12),
    ("🍦", "Ice cream outing", 15),
    ("🧸", "Small toy or treat", 30),
]

FRESH_START_KEY = "fresh_start_v2"


def seed_if_empty(conn) -> bool:
    """Create the family and starter prizes on a brand-new database."""
    created = False
    if not conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]:
        for name, role, color in FAMILY:
            svc.create_member(conn, MemberIn(name=name, role=role, color=color))
        created = True
    if svc.get_setting(conn, "prizes_seeded") is None:
        if not conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0]:
            conn.executemany("INSERT INTO prizes (emoji, title, cost) VALUES (?, ?, ?)", STARTER_PRIZES)
        svc.set_setting(conn, "prizes_seeded", "1")
    return created


def fresh_start_once(conn) -> bool:
    """Version 2 upgrade: clear the old sample events/tasks one time (family members stay)."""
    if svc.get_setting(conn, FRESH_START_KEY) is not None:
        return False
    svc.clear_data(conn, "activities")
    svc.clear_data(conn, "rewards")
    svc.set_setting(conn, FRESH_START_KEY, "done")
    return True


def reset_pin_if_requested(conn, folder: Path) -> bool:
    """Forgot the parent PIN? Put a file named RESET-PIN.txt in the app folder and restart."""
    flag = folder / "RESET-PIN.txt"
    if not flag.exists():
        return False
    svc.set_setting(conn, "parent_pin", None)
    try:
        flag.unlink()
    except OSError:
        pass
    return True
