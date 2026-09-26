"""All the family-organizer logic lives here, independent of the web framework."""
import base64
import calendar
import datetime as dt
import re
import hashlib
import secrets
import sqlite3
from typing import Iterator, Optional

from .schemas import BonusIn, EventIn, MemberIn, PrizeIn, TaskIn

MAX_RANGE_DAYS = 100
MONTH_STEPS = {"monthly": 1, "quarterly": 3, "semiannual": 6, "yearly": 12}


class NotFoundError(Exception):
    pass


class InvalidError(Exception):
    pass


# ---------------------------------------------------------------- recurrence
def occurs_on(rec: str, start: dt.date, until: Optional[dt.date], day: dt.date) -> bool:
    if day < start or (until and day > until):
        return False
    if rec == "none":
        return day == start
    if rec == "daily":
        return True
    if rec == "weekdays":
        return day.weekday() < 5
    if rec == "weekly":
        return day.weekday() == start.weekday()
    if rec == "biweekly":
        return (day - start).days % 14 == 0
    step = MONTH_STEPS.get(rec)
    if step:
        months = (day.year - start.year) * 12 + day.month - start.month
        if months % step:
            return False
        last_day = calendar.monthrange(day.year, day.month)[1]
        return day.day == min(start.day, last_day)  # the 31st falls back to the month's last day
    return False


def previous_occurrence(rec, start, until, before: dt.date, lookback: int = 400) -> Optional[dt.date]:
    """Most recent occurrence strictly before `before`."""
    day = before - dt.timedelta(days=1)
    stop = max(start, before - dt.timedelta(days=lookback))
    while day >= stop:
        if occurs_on(rec, start, until, day):
            return day
        day -= dt.timedelta(days=1)
    return None


def occurrences(rec, start, until, range_start, range_end) -> Iterator[dt.date]:
    day = max(start, range_start)
    last = min(range_end, until) if until else range_end
    while day <= last:
        if occurs_on(rec, start, until, day):
            yield day
        day += dt.timedelta(days=1)


# ------------------------------------------------------------------- helpers
def _d(s: Optional[str]) -> Optional[dt.date]:
    return dt.date.fromisoformat(s) if s else None


def _t(t: Optional[dt.time]) -> Optional[str]:
    return t.strftime("%H:%M") if t else None


def _row(r: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(r) if r is not None else None


def _check_member(conn, member_id: Optional[int]) -> None:
    if member_id is not None and not conn.execute(
        "SELECT 1 FROM members WHERE id = ?", (member_id,)
    ).fetchone():
        raise InvalidError("That family member doesn't exist")


def check_range(start: dt.date, end: dt.date) -> None:
    if end < start:
        raise InvalidError("end must be on or after start")
    if (end - start).days > MAX_RANGE_DAYS:
        raise InvalidError(f"Date range can be at most {MAX_RANGE_DAYS} days")


# ------------------------------------------------------------------- members
# Everything except the photo bytes (those are served separately and cached by the browser)
MEMBER_COLS = ("id, name, role, color, emoji, sort_order, photo_version, "
               "(photo IS NOT NULL AND length(photo) > 0) AS has_photo")


def _member(r) -> dict:
    m = dict(r)
    m["has_photo"] = bool(m["has_photo"])
    return m


def list_members(conn) -> list[dict]:
    return [_member(r) for r in conn.execute(f"SELECT {MEMBER_COLS} FROM members ORDER BY sort_order, id")]


def get_member(conn, member_id: int) -> dict:
    r = conn.execute(f"SELECT {MEMBER_COLS} FROM members WHERE id = ?", (member_id,)).fetchone()
    if not r:
        raise NotFoundError("Family member not found")
    return _member(r)


PHOTO_MAX_BYTES = 2_000_000
_DATA_URL = re.compile(r"^data:image/[a-z+.-]+;base64,(?P<b64>[A-Za-z0-9+/=\s]+)$")


def _sniff_image(raw: bytes) -> Optional[str]:
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def set_photo(conn, member_id: int, data_url: str) -> dict:
    """Save a profile picture sent as a data: URL (the browser crops & shrinks it first)."""
    get_member(conn, member_id)
    m = _DATA_URL.match(data_url.strip())
    if not m:
        raise InvalidError("Please choose a JPG, PNG or WebP picture")
    try:
        raw = base64.b64decode(m.group("b64"), validate=False)
    except ValueError:
        raise InvalidError("That picture couldn't be read")
    if len(raw) > PHOTO_MAX_BYTES:
        raise InvalidError("That picture is too big — try a smaller one")
    mime = _sniff_image(raw)
    if not mime:
        raise InvalidError("Please choose a JPG, PNG or WebP picture")
    conn.execute(
        "UPDATE members SET photo = ?, photo_mime = ?, photo_version = photo_version + 1 WHERE id = ?",
        (raw, mime, member_id),
    )
    conn.commit()
    return get_member(conn, member_id)


def clear_photo(conn, member_id: int) -> dict:
    get_member(conn, member_id)
    conn.execute(
        "UPDATE members SET photo = NULL, photo_mime = '', photo_version = photo_version + 1 WHERE id = ?",
        (member_id,),
    )
    conn.commit()
    return get_member(conn, member_id)


def get_photo(conn, member_id: int) -> tuple[bytes, str]:
    r = conn.execute("SELECT photo, photo_mime FROM members WHERE id = ?", (member_id,)).fetchone()
    if not r or not r["photo"]:
        raise NotFoundError("No photo")
    return bytes(r["photo"]), r["photo_mime"] or "image/jpeg"


def create_member(conn, data: MemberIn) -> dict:
    nxt = conn.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM members").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO members (name, role, color, emoji, sort_order) VALUES (?, ?, ?, ?, ?)",
        (data.name, data.role, data.color, data.emoji.strip(), nxt),
    )
    conn.commit()
    return get_member(conn, cur.lastrowid)


def update_member(conn, member_id: int, data: MemberIn) -> dict:
    get_member(conn, member_id)
    conn.execute(
        "UPDATE members SET name = ?, role = ?, color = ?, emoji = ? WHERE id = ?",
        (data.name, data.role, data.color, data.emoji.strip(), member_id),
    )
    conn.commit()
    return get_member(conn, member_id)


def delete_member(conn, member_id: int) -> None:
    """Their events and tasks are kept and move to the whole family."""
    get_member(conn, member_id)
    conn.execute("UPDATE events SET member_id = NULL WHERE member_id = ?", (member_id,))
    conn.execute("UPDATE tasks SET member_id = NULL WHERE member_id = ?", (member_id,))
    # take them out of any chore rotation
    for t in conn.execute("SELECT id, rotation FROM tasks WHERE rotation != ''").fetchall():
        ids = [i for i in _rotation(t["rotation"]) if i != member_id]
        conn.execute(
            "UPDATE tasks SET rotation = ?, member_id = COALESCE(member_id, ?) WHERE id = ?",
            (",".join(map(str, ids)) if len(ids) > 1 else "", ids[0] if ids else None, t["id"]),
        )
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()


# -------------------------------------------------------------------- events
def get_event(conn, event_id: int) -> dict:
    e = _row(conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone())
    if not e:
        raise NotFoundError("Event not found")
    return e


def _event_values(data: EventIn):
    return (
        data.title, data.member_id, data.start_date.isoformat(), _t(data.start_time),
        _t(data.end_time), data.location.strip(), data.notes.strip(), data.recurrence,
        data.recurrence_end.isoformat() if data.recurrence_end else None,
    )


def create_event(conn, data: EventIn) -> dict:
    _check_member(conn, data.member_id)
    cur = conn.execute(
        """INSERT INTO events (title, member_id, start_date, start_time, end_time,
               location, notes, recurrence, recurrence_end)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        _event_values(data),
    )
    conn.commit()
    return get_event(conn, cur.lastrowid)


def update_event(conn, event_id: int, data: EventIn) -> dict:
    get_event(conn, event_id)
    _check_member(conn, data.member_id)
    conn.execute(
        """UPDATE events SET title = ?, member_id = ?, start_date = ?, start_time = ?,
               end_time = ?, location = ?, notes = ?, recurrence = ?, recurrence_end = ?
           WHERE id = ?""",
        (*_event_values(data), event_id),
    )
    conn.commit()
    return get_event(conn, event_id)


def delete_event(conn, event_id: int) -> None:
    get_event(conn, event_id)
    conn.execute("DELETE FROM event_completions WHERE event_id = ?", (event_id,))
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()


def event_occurrences(conn, start: dt.date, end: dt.date) -> list[dict]:
    """Every event instance between start and end (inclusive), repeats expanded."""
    check_range(start, end)
    rows = conn.execute(
        """SELECT * FROM events
           WHERE start_date <= ?
             AND (recurrence != 'none' OR start_date >= ?)
             AND (recurrence_end IS NULL OR recurrence_end >= ?)""",
        (end.isoformat(), start.isoformat(), start.isoformat()),
    ).fetchall()
    done = {
        (r["event_id"], r["on_date"])
        for r in conn.execute(
            "SELECT event_id, on_date FROM event_completions WHERE on_date BETWEEN ? AND ?",
            (start.isoformat(), end.isoformat()),
        )
    }
    out = []
    for r in rows:
        ev = dict(r)
        for day in occurrences(ev["recurrence"], _d(ev["start_date"]), _d(ev["recurrence_end"]), start, end):
            key = day.isoformat()
            out.append({**ev, "date": key, "done": (ev["id"], key) in done})
    # all-day events first, then by start time
    out.sort(key=lambda e: (e["date"], e["start_time"] is not None, e["start_time"] or "", e["title"]))
    return out


def toggle_event(conn, event_id: int, on_date: Optional[dt.date]) -> dict:
    """Mark one occurrence of an event as done (or not done)."""
    ev = get_event(conn, event_id)
    day = on_date or dt.date.today()
    if not occurs_on(ev["recurrence"], _d(ev["start_date"]), _d(ev["recurrence_end"]), day):
        raise InvalidError("That event isn't on the calendar that day")
    key = (event_id, day.isoformat())
    if conn.execute("SELECT 1 FROM event_completions WHERE event_id = ? AND on_date = ?", key).fetchone():
        conn.execute("DELETE FROM event_completions WHERE event_id = ? AND on_date = ?", key)
        now_done = False
    else:
        conn.execute("INSERT INTO event_completions (event_id, on_date) VALUES (?, ?)", key)
        now_done = True
    conn.commit()
    return {"event_id": event_id, "date": day.isoformat(), "done": now_done}


# --------------------------------------------------------------------- tasks
STICKERS = {  # key: (emoji, label, default stars)
    "star": ("⭐", "Star", 1),
    "smiley": ("😊", "Smiley", 1),
    "heart": ("💖", "Heart", 1),
    "rainbow": ("🌈", "Rainbow", 2),
    "rocket": ("🚀", "Rocket", 3),
    "trophy": ("🏆", "Trophy", 5),
}


def _rotation(text: str) -> list[int]:
    return [int(x) for x in (text or "").split(",") if x.strip().isdigit()]


def assignee_for(t: dict, day: dt.date) -> Optional[int]:
    """Who does this task on `day`? Chores with a rotation take turns by day or by week."""
    rot = t.get("rotation", "")
    ids = rot if isinstance(rot, list) else _rotation(rot)
    if len(ids) < 2:
        return t["member_id"]
    start = _d(t["due_date"])
    if t.get("rotate_every") == "day":
        idx = (day - start).days
    else:
        idx = ((day - dt.timedelta(days=day.weekday())) - (start - dt.timedelta(days=start.weekday()))).days // 7
    return ids[idx % len(ids)]


def _items_by_task(conn, task_ids) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {tid: [] for tid in task_ids}
    if not task_ids:
        return out
    marks = ",".join("?" * len(task_ids))
    for r in conn.execute(
        f"SELECT id, task_id, title, position FROM task_items WHERE task_id IN ({marks}) ORDER BY position, id",
        list(task_ids),
    ):
        out[r["task_id"]].append({"id": r["id"], "title": r["title"], "position": r["position"]})
    return out


def _task_out(t: dict) -> dict:
    t["rotation"] = _rotation(t.get("rotation", ""))
    return t


def get_task(conn, task_id: int) -> dict:
    t = _row(conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())
    if not t:
        raise NotFoundError("Task not found")
    t["items"] = _items_by_task(conn, [task_id])[task_id]
    return _task_out(t)


def _task_values(data: TaskIn):
    return (
        data.title, data.member_id, data.due_date.isoformat(), _t(data.due_time),
        data.notes.strip(), data.recurrence,
        data.recurrence_end.isoformat() if data.recurrence_end else None,
        data.category, data.sticker, data.points,
        ",".join(map(str, data.rotation)), data.rotate_every,
    )


def _save_items(conn, task_id: int, items) -> None:
    """Sync the checklist: keep items that still exist (and their check marks),
    rename/reorder them, add new ones, remove the rest."""
    existing = {r[0] for r in conn.execute("SELECT id FROM task_items WHERE task_id = ?", (task_id,))}
    kept = set()
    for pos, it in enumerate(items):
        if it.id in existing:
            conn.execute("UPDATE task_items SET title = ?, position = ? WHERE id = ?", (it.title, pos, it.id))
            kept.add(it.id)
        else:
            conn.execute("INSERT INTO task_items (task_id, title, position) VALUES (?, ?, ?)", (task_id, it.title, pos))
    for gone in existing - kept:
        conn.execute("DELETE FROM task_item_completions WHERE item_id = ?", (gone,))
        conn.execute("DELETE FROM task_items WHERE id = ?", (gone,))


def _check_task_members(conn, data: TaskIn) -> None:
    _check_member(conn, data.member_id)
    for mid in data.rotation:
        _check_member(conn, mid)


def create_task(conn, data: TaskIn) -> dict:
    _check_task_members(conn, data)
    cur = conn.execute(
        """INSERT INTO tasks (title, member_id, due_date, due_time, notes, recurrence, recurrence_end,
               category, sticker, points, rotation, rotate_every)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        _task_values(data),
    )
    _save_items(conn, cur.lastrowid, data.items)
    conn.commit()
    return get_task(conn, cur.lastrowid)


def update_task(conn, task_id: int, data: TaskIn) -> dict:
    get_task(conn, task_id)
    _check_task_members(conn, data)
    conn.execute(
        """UPDATE tasks SET title = ?, member_id = ?, due_date = ?, due_time = ?, notes = ?,
               recurrence = ?, recurrence_end = ?, category = ?, sticker = ?, points = ?,
               rotation = ?, rotate_every = ? WHERE id = ?""",
        (*_task_values(data), task_id),
    )
    _save_items(conn, task_id, data.items)
    conn.commit()
    return get_task(conn, task_id)


def delete_task(conn, task_id: int) -> None:
    get_task(conn, task_id)
    conn.execute(
        "DELETE FROM task_item_completions WHERE item_id IN (SELECT id FROM task_items WHERE task_id = ?)",
        (task_id,),
    )
    conn.execute("DELETE FROM task_items WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM task_completions WHERE task_id = ?", (task_id,))
    conn.execute("UPDATE rewards SET task_id = NULL WHERE task_id = ?", (task_id,))  # keep earned stars
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


def _completions(conn, task_ids=None) -> dict[int, set[str]]:
    out: dict[int, set[str]] = {}
    for r in conn.execute("SELECT task_id, on_date FROM task_completions"):
        out.setdefault(r["task_id"], set()).add(r["on_date"])
    return out


def tasks_for_day(conn, day: dt.date, today: Optional[dt.date] = None, category: Optional[str] = None) -> list[dict]:
    """Tasks due on `day`, each with `done`, its checklist items, and who does it that day.
    When `day` is today, missed one-off tasks and missed home-maintenance jobs carry over as overdue."""
    today = today or dt.date.today()
    rows = conn.execute(
        """SELECT * FROM tasks WHERE due_date <= ?
           AND (recurrence_end IS NULL OR recurrence_end >= ? OR (category = 'maintenance' AND ? = ?))""",
        (day.isoformat(), day.isoformat(), day.isoformat(), today.isoformat()),
    ).fetchall()
    if not rows:
        return []
    done = _completions(conn)

    out = []
    for r in rows:
        t = dict(r)
        if category and t["category"] != category:
            continue
        due, until = _d(t["due_date"]), _d(t["recurrence_end"])
        comps = done.get(t["id"], set())
        occ_day = None
        overdue = False
        if occurs_on(t["recurrence"], due, until, day):
            occ_day = day
        elif day == today and t["recurrence"] == "none" and due < day and t["due_date"] not in comps:
            occ_day, overdue = due, True
        elif day == today and t["category"] == "maintenance" and t["recurrence"] not in ("none", "daily", "weekdays"):
            prev = previous_occurrence(t["recurrence"], due, until, day)
            if prev and not any(c >= prev.isoformat() for c in comps):
                occ_day, overdue = prev, True
        if occ_day is None:
            continue
        key = occ_day.isoformat()
        t.update(date=key, done=key in comps, overdue=overdue)
        t["member_id"] = assignee_for(t, occ_day)
        out.append(_task_out(t))

    items = _items_by_task(conn, [t["id"] for t in out])
    all_ids = [i["id"] for lst in items.values() for i in lst]
    item_done = set()
    if all_ids:
        marks = ",".join("?" * len(all_ids))
        item_done = {
            (r["item_id"], r["on_date"])
            for r in conn.execute(
                f"SELECT item_id, on_date FROM task_item_completions WHERE item_id IN ({marks})", all_ids
            )
        }
    for t in out:
        t["items"] = [{**i, "done": (i["id"], t["date"]) in item_done} for i in items[t["id"]]]
        t["items_total"] = len(t["items"])
        t["items_done"] = sum(i["done"] for i in t["items"])

    out.sort(key=lambda t: (not t["overdue"], t["due_time"] is None, t["due_time"] or "", t["title"]))
    return out


def _completion_day(t: dict, on_date: Optional[dt.date]) -> dt.date:
    due = _d(t["due_date"])
    if t["recurrence"] == "none":
        return due  # one-off tasks are always completed against their due date
    day = on_date or dt.date.today()
    if not occurs_on(t["recurrence"], due, _d(t["recurrence_end"]), day):
        raise InvalidError("That task isn't scheduled on this day")
    return day


def _set_task_done(conn, t: dict, day: str, done: bool) -> Optional[dict]:
    """Mark a task occurrence done/undone and give/take back its stars. Returns the reward given."""
    if done:
        conn.execute("INSERT OR IGNORE INTO task_completions (task_id, on_date) VALUES (?, ?)", (t["id"], day))
        return _award(conn, t, day)
    conn.execute("DELETE FROM task_completions WHERE task_id = ? AND on_date = ?", (t["id"], day))
    conn.execute("DELETE FROM rewards WHERE kind = 'earn' AND task_id = ? AND on_date = ?", (t["id"], day))
    return None


def toggle_task(conn, task_id: int, on_date: Optional[dt.date]) -> dict:
    """Check/uncheck a whole task. Its checklist items follow along."""
    t = get_task(conn, task_id)
    day = _completion_day(t, on_date).isoformat()
    was_done = conn.execute(
        "SELECT 1 FROM task_completions WHERE task_id = ? AND on_date = ?", (task_id, day)
    ).fetchone() is not None
    now_done = not was_done
    reward = _set_task_done(conn, t, day, now_done)
    for item in t["items"]:
        if now_done:
            conn.execute("INSERT OR IGNORE INTO task_item_completions (item_id, on_date) VALUES (?, ?)", (item["id"], day))
        else:
            conn.execute("DELETE FROM task_item_completions WHERE item_id = ? AND on_date = ?", (item["id"], day))
    conn.commit()
    return {"task_id": task_id, "date": day, "done": now_done, "reward": reward}


def toggle_item(conn, task_id: int, item_id: int, on_date: Optional[dt.date]) -> dict:
    """Check/uncheck one checklist item. The task completes when every item is checked."""
    t = get_task(conn, task_id)
    if item_id not in {i["id"] for i in t["items"]}:
        raise NotFoundError("Checklist item not found")
    day = _completion_day(t, on_date).isoformat()
    key = (item_id, day)
    if conn.execute("SELECT 1 FROM task_item_completions WHERE item_id = ? AND on_date = ?", key).fetchone():
        conn.execute("DELETE FROM task_item_completions WHERE item_id = ? AND on_date = ?", key)
        item_done = False
    else:
        conn.execute("INSERT INTO task_item_completions (item_id, on_date) VALUES (?, ?)", key)
        item_done = True
    ids = [i["id"] for i in t["items"]]
    marks = ",".join("?" * len(ids))
    done_count = conn.execute(
        f"SELECT COUNT(*) FROM task_item_completions WHERE on_date = ? AND item_id IN ({marks})", [day, *ids]
    ).fetchone()[0]
    task_done = done_count == len(ids)
    was_done = conn.execute(
        "SELECT 1 FROM task_completions WHERE task_id = ? AND on_date = ?", (task_id, day)
    ).fetchone() is not None
    reward = _set_task_done(conn, t, day, task_done) if task_done != was_done else None
    conn.commit()
    return {"task_id": task_id, "item_id": item_id, "date": day, "done": item_done,
            "task_done": task_done, "items_done": done_count, "items_total": len(ids), "reward": reward}


# ------------------------------------------------------------------- rewards
BADGES = [  # key, emoji, name, how to earn, test(stats)
    ("first-task", "🌟", "First Star", "Finish your first task", lambda s: s["tasks"] >= 1),
    ("ten-tasks", "🎈", "Busy Bee", "Finish 10 tasks", lambda s: s["tasks"] >= 10),
    ("fifty-tasks", "🦄", "Super Helper", "Finish 50 tasks", lambda s: s["tasks"] >= 50),
    ("hundred-tasks", "👑", "Task Royalty", "Finish 100 tasks", lambda s: s["tasks"] >= 100),
    ("streak-3", "🔥", "On Fire", "3-day streak", lambda s: s["streak"] >= 3),
    ("streak-7", "⚡", "Week Warrior", "7-day streak", lambda s: s["streak"] >= 7),
    ("streak-30", "🚀", "Unstoppable", "30-day streak", lambda s: s["streak"] >= 30),
    ("stars-50", "💫", "Star Collector", "Earn 50 stars", lambda s: s["stars"] >= 50),
    ("stars-200", "🌌", "Galaxy Hero", "Earn 200 stars", lambda s: s["stars"] >= 200),
    ("chores-10", "🧹", "Chore Champ", "Finish 10 chores", lambda s: s["chores"] >= 10),
    ("maint-5", "🛠️", "Home Hero", "Finish 5 home-maintenance jobs", lambda s: s["maintenance"] >= 5),
    ("first-prize", "🎁", "Treat Yourself", "Cash in your first prize", lambda s: s["prizes"] >= 1),
]
BADGE_INFO = {b[0]: {"key": b[0], "emoji": b[1], "name": b[2], "how": b[3]} for b in BADGES}


def _award(conn, t: dict, day: str) -> Optional[dict]:
    member_id = assignee_for(t, _d(day))
    if member_id is None or t.get("points", 0) <= 0:
        return None  # "Everyone" tasks are celebrated but don't give personal stars
    conn.execute(
        """INSERT OR IGNORE INTO rewards (member_id, kind, points, sticker, task_id, on_date, note)
           VALUES (?, 'earn', ?, ?, ?, ?, ?)""",
        (member_id, t["points"], t["sticker"], t["id"], day, t["title"]),
    )
    new_badges = check_badges(conn, member_id)
    return {"member_id": member_id, "points": t["points"], "sticker": t["sticker"],
            "emoji": STICKERS[t["sticker"]][0], "balance": balance(conn, member_id),
            "streak": streak(conn, member_id), "new_badges": new_badges}


def balance(conn, member_id: int) -> int:
    earned = conn.execute("SELECT COALESCE(SUM(points), 0) FROM rewards WHERE member_id = ?", (member_id,)).fetchone()[0]
    spent = conn.execute(
        "SELECT COALESCE(SUM(cost), 0) FROM redemptions WHERE member_id = ? AND status IN ('pending', 'approved')",
        (member_id,),
    ).fetchone()[0]
    return earned - spent


def streak(conn, member_id: int, today: Optional[dt.date] = None) -> int:
    """Days in a row (ending today, or yesterday if today isn't done yet) with at least one finished task."""
    today = today or dt.date.today()
    days = {r[0] for r in conn.execute(
        "SELECT DISTINCT on_date FROM rewards WHERE member_id = ? AND kind = 'earn' AND on_date <= ?",
        (member_id, today.isoformat()),
    )}
    day = today if today.isoformat() in days else today - dt.timedelta(days=1)
    n = 0
    while day.isoformat() in days:
        n += 1
        day -= dt.timedelta(days=1)
    return n


def _stats(conn, member_id: int) -> dict:
    q = lambda sql: conn.execute(sql, (member_id,)).fetchone()[0]
    return {
        "tasks": q("SELECT COUNT(*) FROM rewards WHERE member_id = ? AND kind = 'earn'"),
        "stars": q("SELECT COALESCE(SUM(points), 0) FROM rewards WHERE member_id = ?"),
        "chores": q("""SELECT COUNT(*) FROM rewards r JOIN tasks t ON t.id = r.task_id
                       WHERE r.member_id = ? AND r.kind = 'earn' AND t.category = 'chore'"""),
        "maintenance": q("""SELECT COUNT(*) FROM rewards r JOIN tasks t ON t.id = r.task_id
                            WHERE r.member_id = ? AND r.kind = 'earn' AND t.category = 'maintenance'"""),
        "prizes": q("SELECT COUNT(*) FROM redemptions WHERE member_id = ? AND status = 'approved'"),
        "streak": streak(conn, member_id),
    }


def check_badges(conn, member_id: int) -> list[dict]:
    """Unlock any badges newly earned; returns the new ones."""
    stats = _stats(conn, member_id)
    have = {r[0] for r in conn.execute("SELECT badge FROM badges_earned WHERE member_id = ?", (member_id,))}
    new = []
    for key, *_rest, test in BADGES:
        if key not in have and test(stats):
            conn.execute("INSERT OR IGNORE INTO badges_earned (member_id, badge) VALUES (?, ?)", (member_id, key))
            new.append(BADGE_INFO[key])
    return new


def week_bounds(day: dt.date) -> tuple[dt.date, dt.date]:
    start = day - dt.timedelta(days=day.weekday())
    return start, start + dt.timedelta(days=6)


def rewards_overview(conn, today: Optional[dt.date] = None) -> dict:
    today = today or dt.date.today()
    ws, we = week_bounds(today)
    members = []
    for m in list_members(conn):
        mid = m["id"]
        week = conn.execute(
            "SELECT COALESCE(SUM(points), 0) FROM rewards WHERE member_id = ? AND on_date BETWEEN ? AND ?",
            (mid, ws.isoformat(), we.isoformat()),
        ).fetchone()[0]
        earned = {r["badge"]: r["earned_at"] for r in conn.execute(
            "SELECT badge, earned_at FROM badges_earned WHERE member_id = ?", (mid,))}
        stats = _stats(conn, mid)
        members.append({
            "member": m, "balance": balance(conn, mid), "streak": stats["streak"],
            "week_stars": week, "total_stars": stats["stars"], "tasks_done": stats["tasks"],
            "badges": [{**BADGE_INFO[k], "earned": k in earned, "earned_at": earned.get(k)} for k, *_ in BADGES],
        })
    top = max((m["week_stars"] for m in members), default=0)
    for m in members:
        m["star_of_week"] = top > 0 and m["week_stars"] == top
    return {"week_start": ws.isoformat(), "week_end": we.isoformat(), "members": members,
            "stickers": {k: {"emoji": v[0], "label": v[1], "points": v[2]} for k, v in STICKERS.items()}}


def recent_rewards(conn, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """SELECT id, member_id, kind, points, sticker, on_date, note, created_at FROM rewards
           ORDER BY created_at DESC, id DESC LIMIT ?""", (limit,)).fetchall()
    return [{**dict(r), "emoji": STICKERS.get(r["sticker"], ("⭐",))[0]} for r in rows]


def give_bonus(conn, data: BonusIn) -> dict:
    get_member(conn, data.member_id)
    conn.execute(
        "INSERT INTO rewards (member_id, kind, points, sticker, on_date, note) VALUES (?, 'bonus', ?, ?, ?, ?)",
        (data.member_id, data.points, data.sticker, dt.date.today().isoformat(), data.note.strip() or "Bonus from a grown-up"),
    )
    new_badges = check_badges(conn, data.member_id)
    conn.commit()
    return {"member_id": data.member_id, "points": data.points, "sticker": data.sticker,
            "emoji": STICKERS[data.sticker][0], "balance": balance(conn, data.member_id),
            "streak": streak(conn, data.member_id), "new_badges": new_badges}


# -------------------------------------------------------------------- prizes
def list_prizes(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM prizes WHERE active = 1 ORDER BY cost, title")]


def _get_prize(conn, prize_id: int) -> dict:
    p = _row(conn.execute("SELECT * FROM prizes WHERE id = ? AND active = 1", (prize_id,)).fetchone())
    if not p:
        raise NotFoundError("Prize not found")
    return p


def create_prize(conn, data: PrizeIn) -> dict:
    cur = conn.execute("INSERT INTO prizes (title, emoji, cost) VALUES (?, ?, ?)",
                       (data.title, data.emoji.strip() or "🎁", data.cost))
    conn.commit()
    return _get_prize(conn, cur.lastrowid)


def update_prize(conn, prize_id: int, data: PrizeIn) -> dict:
    _get_prize(conn, prize_id)
    conn.execute("UPDATE prizes SET title = ?, emoji = ?, cost = ? WHERE id = ?",
                 (data.title, data.emoji.strip() or "🎁", data.cost, prize_id))
    conn.commit()
    return _get_prize(conn, prize_id)


def delete_prize(conn, prize_id: int) -> None:
    _get_prize(conn, prize_id)
    conn.execute("UPDATE prizes SET active = 0 WHERE id = ?", (prize_id,))  # keeps history intact
    conn.commit()


def request_prize(conn, member_id: int, prize_id: int) -> dict:
    get_member(conn, member_id)
    p = _get_prize(conn, prize_id)
    have = balance(conn, member_id)
    if have < p["cost"]:
        raise InvalidError(f"Needs {p['cost']} stars — only {have} so far. Keep going!")
    cur = conn.execute(
        "INSERT INTO redemptions (member_id, prize_id, prize_title, prize_emoji, cost) VALUES (?, ?, ?, ?, ?)",
        (member_id, p["id"], p["title"], p["emoji"], p["cost"]),
    )
    conn.commit()
    return {**dict(conn.execute("SELECT * FROM redemptions WHERE id = ?", (cur.lastrowid,)).fetchone()),
            "balance": balance(conn, member_id)}


def list_redemptions(conn, status: Optional[str] = None, limit: int = 30) -> list[dict]:
    sql = "SELECT * FROM redemptions"
    args: list = []
    if status:
        sql += " WHERE status = ?"
        args.append(status)
    sql += " ORDER BY requested_at DESC, id DESC LIMIT ?"
    args.append(limit)
    return [dict(r) for r in conn.execute(sql, args)]


def decide_redemption(conn, redemption_id: int, approve: bool) -> dict:
    r = _row(conn.execute("SELECT * FROM redemptions WHERE id = ?", (redemption_id,)).fetchone())
    if not r:
        raise NotFoundError("Request not found")
    if r["status"] != "pending":
        raise InvalidError("That request was already answered")
    conn.execute(
        "UPDATE redemptions SET status = ?, decided_at = datetime('now') WHERE id = ?",
        ("approved" if approve else "declined", redemption_id),
    )
    new_badges = check_badges(conn, r["member_id"]) if approve else []
    conn.commit()
    return {**dict(conn.execute("SELECT * FROM redemptions WHERE id = ?", (redemption_id,)).fetchone()),
            "balance": balance(conn, r["member_id"]), "new_badges": new_badges}


# --------------------------------------------------------- home maintenance
REC_LABELS = {
    "none": "One time", "daily": "Daily", "weekdays": "Weekdays", "weekly": "Weekly",
    "biweekly": "Every 2 weeks", "monthly": "Monthly", "quarterly": "Every 3 months",
    "semiannual": "Every 6 months", "yearly": "Yearly",
}

# key, emoji, title, recurrence, tip
MAINTENANCE_STARTER = [
    ("dishes", "🍽️", "Run & empty the dishwasher", "daily", "Quick daily reset for the kitchen."),
    ("counters", "🧽", "Wipe kitchen counters & sink", "daily", ""),
    ("trash", "🗑️", "Take out trash & recycling", "weekly", "Check your pickup day."),
    ("pool-test", "🏊", "Test pool water & add chemicals", "weekly", "Chlorine 1–3 ppm, pH 7.2–7.6."),
    ("pool-skimmer", "🍃", "Empty pool skimmer & pump baskets", "weekly", ""),
    ("bathrooms", "🚿", "Clean bathrooms", "weekly", ""),
    ("sheets", "🛏️", "Wash bed sheets & towels", "weekly", ""),
    ("fridge-clean", "🥬", "Clear out old food from the fridge", "weekly", ""),
    ("air-filter", "🌬️", "Change HVAC air filter", "monthly", "Write your filter size in the notes. Every 1–3 months; monthly with pets."),
    ("smoke-test", "🚨", "Test smoke & carbon monoxide alarms", "monthly", "Press the test button on each alarm."),
    ("disposal", "🍋", "Clean garbage disposal", "monthly", "Ice cubes + lemon peels work great."),
    ("range-hood", "🍳", "Clean range hood filter", "monthly", ""),
    ("fire-ext", "🧯", "Check fire extinguisher gauge", "monthly", "Needle should be in the green."),
    ("water-softener", "🧂", "Check water softener salt", "monthly", ""),
    ("dishwasher-filter", "🫧", "Clean dishwasher filter", "quarterly", ""),
    ("gfci", "🔌", "Test GFCI outlets", "quarterly", "Press TEST, then RESET."),
    ("drains", "🚰", "Clean slow drains & run water in unused ones", "quarterly", ""),
    ("pest", "🐜", "Pest control check / treatment", "quarterly", ""),
    ("hvac-service", "❄️", "HVAC tune-up (spring cooling / fall heating)", "semiannual", "Schedule before summer and before winter."),
    ("fridge-filter", "💧", "Replace refrigerator water filter", "semiannual", ""),
    ("dryer-vent", "👕", "Clean dryer vent & lint duct", "semiannual", "Lint buildup is a fire risk."),
    ("gutters", "🍂", "Clean gutters & downspouts", "semiannual", "Spring and fall."),
    ("fans", "🌀", "Reverse ceiling fans & dust blades", "semiannual", "Counter-clockwise in summer, clockwise in winter."),
    ("windows", "🪟", "Wash windows & screens", "semiannual", ""),
    ("coils", "🧊", "Vacuum refrigerator coils", "yearly", ""),
    ("water-heater", "🔥", "Flush the water heater", "yearly", "Removes sediment so it lasts longer."),
    ("alarm-batteries", "🔋", "Replace smoke/CO alarm batteries", "yearly", "Replace whole alarms every 10 years."),
    ("roof", "🏠", "Inspect roof, attic & siding", "yearly", ""),
    ("garage", "🚗", "Lubricate & test garage door", "yearly", ""),
    ("caulk", "🛁", "Check caulking around tubs, sinks & windows", "yearly", ""),
    ("termite", "🪵", "Termite inspection", "yearly", ""),
    ("pool-open", "☀️", "Pool equipment check & service", "yearly", ""),
]
STARTER_BY_KEY = {k: (e, t, r, tip) for k, e, t, r, tip in MAINTENANCE_STARTER}


def maintenance_starter(conn) -> list[dict]:
    existing = {r[0].lower() for r in conn.execute("SELECT title FROM tasks WHERE category = 'maintenance'")}
    return [{"key": k, "emoji": e, "title": t, "recurrence": r, "label": REC_LABELS[r], "tip": tip,
             "added": f"{e} {t}".lower() in existing} for k, e, t, r, tip in MAINTENANCE_STARTER]


def add_maintenance_starter(conn, keys: list[str], member_id: Optional[int], start: Optional[dt.date]) -> int:
    _check_member(conn, member_id)
    start = start or dt.date.today()
    existing = {r[0].lower() for r in conn.execute("SELECT title FROM tasks WHERE category = 'maintenance'")}
    added = 0
    for key in keys:
        if key not in STARTER_BY_KEY:
            continue
        emoji, title, rec, tip = STARTER_BY_KEY[key]
        full_title = f"{emoji} {title}"
        if full_title.lower() in existing:
            continue
        points = {"daily": 1, "weekly": 2, "monthly": 3}.get(rec, 5)
        sticker = {1: "star", 2: "rainbow", 3: "rocket"}.get(points, "trophy")
        conn.execute(
            """INSERT INTO tasks (title, member_id, due_date, notes, recurrence, category, sticker, points)
               VALUES (?, ?, ?, ?, ?, 'maintenance', ?, ?)""",
            (full_title, member_id, start.isoformat(), tip, rec, sticker, points),
        )
        existing.add(full_title.lower())
        added += 1
    conn.commit()
    return added


def maintenance_overview(conn, today: Optional[dt.date] = None) -> list[dict]:
    """Every maintenance job with when it was last done and when it's due next."""
    today = today or dt.date.today()
    comps = _completions(conn)
    out = []
    for r in conn.execute("SELECT * FROM tasks WHERE category = 'maintenance'").fetchall():
        t = _task_out(dict(r))
        start, until, rec = _d(t["due_date"]), _d(t["recurrence_end"]), t["recurrence"]
        done = sorted(comps.get(t["id"], set()))
        last_done = done[-1] if done else None
        overdue = False
        if rec == "none":
            due = start if t["due_date"] not in done else None
            overdue = bool(due and due < today)
        else:
            prev = previous_occurrence(rec, start, until, today)
            if prev and not any(c >= prev.isoformat() for c in done):
                due, overdue = prev, True
            else:
                due = next((d for d in occurrences(rec, start, until, today, today + dt.timedelta(days=800))
                            if d.isoformat() not in done), None)
        t.update(
            last_done=last_done, due=due.isoformat() if due else None, overdue=overdue,
            days_until=(due - today).days if due else None, label=REC_LABELS.get(rec, rec),
            member_id=assignee_for(t, due or today),
        )
        out.append(t)
    order = list(REC_LABELS)
    out.sort(key=lambda t: (order.index(t["recurrence"]) if t["recurrence"] in order else 99,
                            t["days_until"] if t["days_until"] is not None else 9999, t["title"]))
    return out


# ------------------------------------------------------------ settings & PIN
def get_setting(conn, key: str, default: Optional[str] = None) -> Optional[str]:
    r = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(conn, key: str, value: Optional[str]) -> None:
    if value is None:
        conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))
    else:
        conn.execute("INSERT INTO app_settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    conn.commit()


def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 100_000).hex()


def pin_is_set(conn) -> bool:
    return get_setting(conn, "parent_pin") is not None


def pin_ok(conn, pin: Optional[str]) -> bool:
    """True when no PIN is set, or the given PIN matches."""
    stored = get_setting(conn, "parent_pin")
    if stored is None:
        return True
    salt, digest = stored.split("$", 1)
    return bool(pin) and secrets.compare_digest(_hash_pin(pin, salt), digest)


def set_pin(conn, pin: Optional[str], current: Optional[str]) -> None:
    if pin_is_set(conn) and not pin_ok(conn, current):
        raise InvalidError("The current PIN isn't right")
    if pin is None:
        set_setting(conn, "parent_pin", None)
        return
    salt = secrets.token_hex(8)
    set_setting(conn, "parent_pin", f"{salt}${_hash_pin(pin, salt)}")


def clear_data(conn, what: str) -> None:
    """'activities' = all events and tasks (family members & prizes stay).
    'rewards' = all stars, badges and prize requests."""
    if what == "activities":
        for table in ("task_item_completions", "task_items", "task_completions", "event_completions"):
            conn.execute(f"DELETE FROM {table}")
        conn.execute("UPDATE rewards SET task_id = NULL")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM events")
    elif what == "rewards":
        for table in ("rewards", "redemptions", "badges_earned"):
            conn.execute(f"DELETE FROM {table}")
    conn.commit()


# ----------------------------------------------------------- summary/search
def summary(conn, day: dt.date) -> dict:
    tasks = tasks_for_day(conn, day)
    events = event_occurrences(conn, day, day)
    members = []
    for m in list_members(conn):
        mine = [t for t in tasks if t["member_id"] == m["id"]]
        members.append({
            "member": m,
            "tasks_total": len(mine),
            "tasks_done": sum(t["done"] for t in mine),
            # a member's day includes whole-family events too
            "events": sum(e["member_id"] in (m["id"], None) for e in events),
            "events_done": sum(e["done"] for e in events if e["member_id"] in (m["id"], None)),
            "balance": balance(conn, m["id"]),
            "streak": streak(conn, m["id"], day),
        })
    return {
        "date": day.isoformat(),
        "members": members,
        "tasks_total": len(tasks),
        "tasks_done": sum(t["done"] for t in tasks),
        "events_total": len(events),
        "events_done": sum(e["done"] for e in events),
    }


def search(conn, q: str, today: Optional[dt.date] = None, limit: int = 8) -> list[dict]:
    today = today or dt.date.today()
    like = f"%{q.strip()}%"
    results = []
    for e in conn.execute(
        """SELECT * FROM events WHERE title LIKE ? OR location LIKE ? OR notes LIKE ?
           ORDER BY start_date DESC LIMIT ?""", (like, like, like, limit)
    ):
        start, until = _d(e["start_date"]), _d(e["recurrence_end"])
        nxt = next(occurrences(e["recurrence"], start, until, today, today + dt.timedelta(days=60)), None)
        results.append({"type": "event", "id": e["id"], "title": e["title"],
                        "member_id": e["member_id"], "date": (nxt or start).isoformat(),
                        "time": e["start_time"]})
    for t in conn.execute(
        "SELECT * FROM tasks WHERE title LIKE ? OR notes LIKE ? ORDER BY due_date DESC LIMIT ?",
        (like, like, limit),
    ):
        start, until = _d(t["due_date"]), _d(t["recurrence_end"])
        nxt = next(occurrences(t["recurrence"], start, until, today, today + dt.timedelta(days=60)), None)
        results.append({"type": "task", "id": t["id"], "title": t["title"],
                        "member_id": t["member_id"], "date": (nxt or start).isoformat(),
                        "time": t["due_time"]})
    return results
