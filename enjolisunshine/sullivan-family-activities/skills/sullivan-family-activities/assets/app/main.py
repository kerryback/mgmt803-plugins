"""Sullivan Family Activities — FastAPI app.

Run:  uvicorn app.main:app --reload
"""
import datetime as dt
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import services as svc
from .db import connect, get_db, init_db
from .icons import ICONS
from .qr import qr_svg
from .schemas import (BonusIn, ClearIn, EventIn, MemberIn, PinCheck, PinIn, PrizeIn,
                      PhotoIn, RedeemIn, StarterIn, TaskIn, ToggleIn)
from .seed import fresh_start_once, reset_pin_if_requested, seed_if_empty

BASE_DIR = Path(__file__).resolve().parent

# (key, label, url, icon)
NAV = [
    ("home", "Home", "/", "home"),
    ("calendar", "Calendar", "/calendar", "calendar"),
    ("tasks", "Tasks", "/tasks", "check"),
    ("chores", "Chores", "/chores", "sparkles"),
    ("maintenance", "Home Upkeep", "/maintenance", "wrench"),
    ("rewards", "Rewards", "/rewards", "trophy"),
    ("kids", "Kid Mode", "/kids", "smile"),
    ("family", "Family Members", "/family", "users"),
    ("meal-plan", "Meal Plan", "/meal-plan", "utensils"),
    ("shopping", "Shopping Lists", "/shopping", "cart"),
    ("notes", "Notes & Docs", "/notes", "file"),
    ("birthdays", "Birthdays", "/birthdays", "cake"),
    ("travel", "Travel", "/travel", "plane"),
    ("settings", "Settings", "/settings", "settings"),
]

# Sections that have a page shell but no feature yet: key -> (subtitle, color)
COMING_SOON = {
    "meal-plan": ("Plan meals for the week", "peach"),
    "shopping": ("Manage your lists", "green"),
    "notes": ("Important notes & documents", "blue"),
    "birthdays": ("Never miss a celebration", "pink"),
    "travel": ("Upcoming trips", "teal"),
}
QUICK_LINKS = [  # key, subtitle, color
    ("rewards", "Stars, prizes & badges", "yellow"),
    ("chores", "Take turns, earn stars", "purple"),
    ("maintenance", "Filters, HVAC & more", "teal"),
    ("kids", "Big buttons for little ones", "pink"),
    ("meal-plan", "Plan meals for the week", "peach"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect()
    try:
        init_db(conn)
        fresh_start_once(conn)
        seed_if_empty(conn)
        reset_pin_if_requested(conn, BASE_DIR.parent)
    finally:
        conn.close()
    yield


app = FastAPI(title="Sullivan Family Activities", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["ICONS"] = ICONS


@app.exception_handler(svc.NotFoundError)
async def _not_found(_: Request, exc: svc.NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(svc.InvalidError)
async def _invalid(_: Request, exc: svc.InvalidError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


def parent_only(request: Request, db) -> None:
    """Grown-up actions need the parent PIN (sent as the X-Parent-Pin header) once one is set."""
    if not svc.pin_ok(db, request.headers.get("x-parent-pin")):
        raise HTTPException(status_code=401, detail="parent_pin_required")


# ------------------------------------------------------------------- pages
def _page(request: Request, template: str, active: str, **ctx) -> HTMLResponse:
    nav_by_key = {k: (label, url, icon) for k, label, url, icon in NAV}
    return templates.TemplateResponse(
        request,
        template,
        {
            "nav": NAV,
            "active": active,
            "page_title": ctx.pop("page_title", None) or nav_by_key[active][0],
            "quick_links": [(k, nav_by_key[k][0], sub, nav_by_key[k][2], color) for k, sub, color in QUICK_LINKS],
            **ctx,
        },
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return _page(request, "home.html", "home")


@app.get("/calendar", response_class=HTMLResponse, include_in_schema=False)
def calendar_page(request: Request):
    return _page(request, "calendar.html", "calendar")


@app.get("/tasks", response_class=HTMLResponse, include_in_schema=False)
def tasks_page(request: Request):
    return _page(request, "tasks.html", "tasks")


@app.get("/chores", response_class=HTMLResponse, include_in_schema=False)
def chores_page(request: Request):
    return _page(request, "chores.html", "chores")


@app.get("/maintenance", response_class=HTMLResponse, include_in_schema=False)
def maintenance_page(request: Request):
    return _page(request, "maintenance.html", "maintenance")


@app.get("/rewards", response_class=HTMLResponse, include_in_schema=False)
def rewards_page(request: Request):
    return _page(request, "rewards.html", "rewards")


@app.get("/family", response_class=HTMLResponse, include_in_schema=False)
def family_page(request: Request):
    return _page(request, "family.html", "family")


@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
def settings_page(request: Request):
    return _page(request, "settings.html", "settings")


@app.get("/kids", response_class=HTMLResponse, include_in_schema=False)
def kids_picker(request: Request):
    return _page(request, "kids.html", "kids", kid_id=None)


@app.get("/kids/{member_id}", response_class=HTMLResponse, include_in_schema=False)
def kids_page(request: Request, member_id: int):
    return _page(request, "kids.html", "kids", kid_id=member_id)


# ---------------------------------------------------------------- members
@app.get("/api/members")
def list_members(db=Depends(get_db)):
    return svc.list_members(db)


@app.post("/api/members", status_code=201)
def create_member(request: Request, data: MemberIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.create_member(db, data)


@app.put("/api/members/{member_id}")
def update_member(request: Request, member_id: int, data: MemberIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.update_member(db, member_id, data)


@app.delete("/api/members/{member_id}", status_code=204)
def delete_member(request: Request, member_id: int, db=Depends(get_db)):
    parent_only(request, db)
    svc.delete_member(db, member_id)
    return Response(status_code=204)


@app.get("/api/members/{member_id}/photo", include_in_schema=False)
def member_photo(member_id: int, db=Depends(get_db)):
    data, mime = svc.get_photo(db, member_id)
    # URLs carry ?v=<photo_version>, so the browser can cache each version for a long time
    return Response(content=data, media_type=mime, headers={"Cache-Control": "public, max-age=31536000"})


@app.put("/api/members/{member_id}/photo")
def set_member_photo(member_id: int, data: PhotoIn, db=Depends(get_db)):
    """Anyone can add their own profile picture (no PIN needed)."""
    return svc.set_photo(db, member_id, data.data)


@app.delete("/api/members/{member_id}/photo")
def delete_member_photo(member_id: int, db=Depends(get_db)):
    return svc.clear_photo(db, member_id)


# ----------------------------------------------------------------- events
@app.get("/api/events")
def list_events(start: dt.date, end: dt.date, db=Depends(get_db)):
    """Event occurrences in [start, end], with repeating events expanded."""
    return svc.event_occurrences(db, start, end)


@app.get("/api/events/{event_id}")
def get_event(event_id: int, db=Depends(get_db)):
    return svc.get_event(db, event_id)


@app.post("/api/events", status_code=201)
def create_event(request: Request, data: EventIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.create_event(db, data)


@app.put("/api/events/{event_id}")
def update_event(request: Request, event_id: int, data: EventIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.update_event(db, event_id, data)


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(request: Request, event_id: int, db=Depends(get_db)):
    parent_only(request, db)
    svc.delete_event(db, event_id)
    return Response(status_code=204)


@app.post("/api/events/{event_id}/toggle")
def toggle_event(event_id: int, body: ToggleIn, db=Depends(get_db)):
    """Mark one occurrence of an event as done / not done."""
    return svc.toggle_event(db, event_id, body.on_date)


# ------------------------------------------------------------------ tasks
@app.get("/api/tasks")
def list_tasks(day: Optional[dt.date] = Query(None, alias="date"), category: Optional[str] = None,
               db=Depends(get_db)):
    """Tasks for one day (default today), each with `done`, checklist items and who does it."""
    return svc.tasks_for_day(db, day or dt.date.today(), category=category)


@app.get("/api/tasks/all")
def all_tasks(category: Optional[str] = None, db=Depends(get_db)):
    """Every task definition (not per-day), e.g. for the Chores page."""
    rows = db.execute("SELECT id FROM tasks" + (" WHERE category = ?" if category else "") + " ORDER BY title",
                      (category,) if category else ()).fetchall()
    return [svc.get_task(db, r[0]) for r in rows]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int, db=Depends(get_db)):
    return svc.get_task(db, task_id)


@app.post("/api/tasks", status_code=201)
def create_task(request: Request, data: TaskIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.create_task(db, data)


@app.put("/api/tasks/{task_id}")
def update_task(request: Request, task_id: int, data: TaskIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.update_task(db, task_id, data)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(request: Request, task_id: int, db=Depends(get_db)):
    parent_only(request, db)
    svc.delete_task(db, task_id)
    return Response(status_code=204)


@app.post("/api/tasks/{task_id}/toggle")
def toggle_task(task_id: int, body: ToggleIn, db=Depends(get_db)):
    """Check/uncheck a whole task (its checklist items follow). Returns any stars earned."""
    return svc.toggle_task(db, task_id, body.on_date)


@app.post("/api/tasks/{task_id}/items/{item_id}/toggle")
def toggle_task_item(task_id: int, item_id: int, body: ToggleIn, db=Depends(get_db)):
    """Check/uncheck one checklist item; the task completes when all items are checked."""
    return svc.toggle_item(db, task_id, item_id, body.on_date)


# ---------------------------------------------------------------- rewards
@app.get("/api/rewards")
def rewards_overview(db=Depends(get_db)):
    """Stars, streaks, badges and Star of the Week for everyone."""
    return svc.rewards_overview(db)


@app.get("/api/rewards/recent")
def recent_rewards(db=Depends(get_db)):
    return svc.recent_rewards(db)


@app.post("/api/rewards/bonus", status_code=201)
def give_bonus(request: Request, data: BonusIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.give_bonus(db, data)


@app.get("/api/prizes")
def list_prizes(db=Depends(get_db)):
    return svc.list_prizes(db)


@app.post("/api/prizes", status_code=201)
def create_prize(request: Request, data: PrizeIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.create_prize(db, data)


@app.put("/api/prizes/{prize_id}")
def update_prize(request: Request, prize_id: int, data: PrizeIn, db=Depends(get_db)):
    parent_only(request, db)
    return svc.update_prize(db, prize_id, data)


@app.delete("/api/prizes/{prize_id}", status_code=204)
def delete_prize(request: Request, prize_id: int, db=Depends(get_db)):
    parent_only(request, db)
    svc.delete_prize(db, prize_id)
    return Response(status_code=204)


@app.get("/api/redemptions")
def list_redemptions(status: Optional[str] = None, db=Depends(get_db)):
    return svc.list_redemptions(db, status)


@app.post("/api/redemptions", status_code=201)
def request_prize(data: RedeemIn, db=Depends(get_db)):
    """Anyone can ask for a prize; a grown-up approves it."""
    return svc.request_prize(db, data.member_id, data.prize_id)


@app.post("/api/redemptions/{redemption_id}/approve")
def approve_prize(request: Request, redemption_id: int, db=Depends(get_db)):
    parent_only(request, db)
    return svc.decide_redemption(db, redemption_id, True)


@app.post("/api/redemptions/{redemption_id}/decline")
def decline_prize(request: Request, redemption_id: int, db=Depends(get_db)):
    parent_only(request, db)
    return svc.decide_redemption(db, redemption_id, False)


# ----------------------------------------------------------- maintenance
@app.get("/api/maintenance")
def maintenance(db=Depends(get_db)):
    """Every home-maintenance job with last done / next due / overdue."""
    return svc.maintenance_overview(db)


@app.get("/api/maintenance/starter")
def maintenance_starter(db=Depends(get_db)):
    return svc.maintenance_starter(db)


@app.post("/api/maintenance/starter", status_code=201)
def add_maintenance_starter(request: Request, data: StarterIn, db=Depends(get_db)):
    parent_only(request, db)
    return {"added": svc.add_maintenance_starter(db, data.keys, data.member_id, data.start_date)}


# ------------------------------------------------------------ PIN/admin
@app.get("/api/pin")
def pin_status(db=Depends(get_db)):
    return {"set": svc.pin_is_set(db)}


@app.post("/api/pin/verify")
def pin_verify(data: PinCheck, db=Depends(get_db)):
    if not svc.pin_ok(db, data.pin):
        raise HTTPException(status_code=401, detail="That PIN isn't right")
    return {"ok": True}


@app.post("/api/pin")
def pin_set(data: PinIn, db=Depends(get_db)):
    svc.set_pin(db, data.pin, data.current_pin)
    return {"set": True}


@app.post("/api/pin/remove")
def pin_remove(data: PinCheck, db=Depends(get_db)):
    svc.set_pin(db, None, data.pin)
    return {"set": False}


@app.post("/api/admin/clear")
def clear_data(request: Request, data: ClearIn, db=Depends(get_db)):
    parent_only(request, db)
    svc.clear_data(db, data.what)
    return {"cleared": data.what}


# ------------------------------------------------------------ phone link
def _lan_ip() -> str | None:
    """This computer's address on the home network (no data is actually sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


@app.get("/api/phone-link")
def phone_link(request: Request):
    """The address a phone on the same Wi-Fi should open."""
    port = request.url.port or 8000
    ip = _lan_ip()
    return {"url": f"http://{ip}:{port}" if ip else None, "port": port,
            "on_phone": request.client is not None and request.client.host not in ("127.0.0.1", "::1", "localhost")}


@app.get("/api/phone-link/qr.svg", include_in_schema=False)
def phone_link_qr(request: Request):
    """QR code of the phone address, drawn locally (no internet needed)."""
    ip = _lan_ip()
    if not ip:
        raise HTTPException(status_code=404, detail="Not connected to a network")
    svg = qr_svg(f"http://{ip}:{request.url.port or 8000}")
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


# --------------------------------------------------------- summary/search
@app.get("/api/summary")
def summary(day: Optional[dt.date] = Query(None, alias="date"), db=Depends(get_db)):
    return svc.summary(db, day or dt.date.today())


@app.get("/api/search")
def search(q: str = Query(min_length=1, max_length=80), db=Depends(get_db)):
    return svc.search(db, q)


# Registered last so it never shadows the routes above.
@app.get("/{section}", response_class=HTMLResponse, include_in_schema=False)
def coming_soon(request: Request, section: str):
    if section not in COMING_SOON:
        raise HTTPException(status_code=404, detail="Page not found")
    subtitle, color = COMING_SOON[section]
    section_icon = next(ic for k, _, _, ic in NAV if k == section)
    return _page(request, "coming_soon.html", section, subtitle=subtitle, color=color,
                 section_icon=section_icon)
