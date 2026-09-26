"""SQLite connection + schema. Uses Python's built-in sqlite3 — no ORM needed."""
import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv(
    "SULLIVAN_DB",
    str(Path(__file__).resolve().parent.parent / "sullivan_family.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'kid',
    color       TEXT    NOT NULL DEFAULT 'pink',
    emoji       TEXT    NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    member_id       INTEGER REFERENCES members(id) ON DELETE SET NULL,
    start_date      TEXT NOT NULL,            -- YYYY-MM-DD
    start_time      TEXT,                     -- HH:MM, NULL = all day
    end_time        TEXT,                     -- HH:MM
    location        TEXT NOT NULL DEFAULT '',
    notes           TEXT NOT NULL DEFAULT '',
    recurrence      TEXT NOT NULL DEFAULT 'none',  -- none | daily | weekdays | weekly
    recurrence_end  TEXT                      -- YYYY-MM-DD or NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    member_id       INTEGER REFERENCES members(id) ON DELETE SET NULL,
    due_date        TEXT NOT NULL,
    due_time        TEXT,
    notes           TEXT NOT NULL DEFAULT '',
    recurrence      TEXT NOT NULL DEFAULT 'none',
    recurrence_end  TEXT
);

-- One row per (task, day) that has been checked off.
CREATE TABLE IF NOT EXISTS task_completions (
    task_id  INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    on_date  TEXT    NOT NULL,
    PRIMARY KEY (task_id, on_date)
);

-- Checklist items inside a task (e.g. "Pack daycare bag" -> diapers, bottles...)
CREATE TABLE IF NOT EXISTS task_items (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id   INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title     TEXT    NOT NULL,
    position  INTEGER NOT NULL DEFAULT 0
);

-- One row per (checklist item, day) that has been checked off.
CREATE TABLE IF NOT EXISTS task_item_completions (
    item_id  INTEGER NOT NULL REFERENCES task_items(id) ON DELETE CASCADE,
    on_date  TEXT    NOT NULL,
    PRIMARY KEY (item_id, on_date)
);

-- One row per (event, day) marked as done.
CREATE TABLE IF NOT EXISTS event_completions (
    event_id  INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    on_date   TEXT    NOT NULL,
    PRIMARY KEY (event_id, on_date)
);

-- Rewards ledger: stars earned from tasks ("earn") or given by a parent ("bonus").
CREATE TABLE IF NOT EXISTS rewards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id   INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL DEFAULT 'earn',     -- earn | bonus
    points      INTEGER NOT NULL DEFAULT 1,
    sticker     TEXT    NOT NULL DEFAULT 'star',
    task_id     INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    on_date     TEXT    NOT NULL,
    note        TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_rewards_task_day ON rewards(task_id, on_date) WHERE kind = 'earn';
CREATE INDEX IF NOT EXISTS ix_rewards_member ON rewards(member_id, on_date);

-- Prize shop
CREATE TABLE IF NOT EXISTS prizes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    emoji   TEXT    NOT NULL DEFAULT '🎁',
    cost    INTEGER NOT NULL DEFAULT 10,
    active  INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS redemptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    prize_id      INTEGER REFERENCES prizes(id) ON DELETE SET NULL,
    prize_title   TEXT    NOT NULL,
    prize_emoji   TEXT    NOT NULL DEFAULT '🎁',
    cost          INTEGER NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'pending',  -- pending | approved | declined
    requested_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    decided_at    TEXT
);

-- Badges are kept once earned
CREATE TABLE IF NOT EXISTS badges_earned (
    member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    badge      TEXT    NOT NULL,
    earned_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (member_id, badge)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_items_task ON task_items(task_id);
CREATE INDEX IF NOT EXISTS ix_events_start ON events(start_date);
CREATE INDEX IF NOT EXISTS ix_tasks_due ON tasks(due_date);
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Columns added after the first version: (table, column, definition)
MIGRATIONS = [
    ("tasks", "category", "TEXT NOT NULL DEFAULT 'task'"),        # task | chore | maintenance
    ("tasks", "sticker", "TEXT NOT NULL DEFAULT 'star'"),
    ("tasks", "points", "INTEGER NOT NULL DEFAULT 1"),
    ("tasks", "rotation", "TEXT NOT NULL DEFAULT ''"),            # comma-separated member ids
    ("tasks", "rotate_every", "TEXT NOT NULL DEFAULT 'week'"),    # day | week
    ("members", "photo", "BLOB"),                                  # profile picture (small JPEG/PNG/WebP)
    ("members", "photo_mime", "TEXT NOT NULL DEFAULT ''"),
    ("members", "photo_version", "INTEGER NOT NULL DEFAULT 0"),   # bumps on change so browsers refresh
]


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, column, definition in MIGRATIONS:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.commit()


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
