"""Request bodies, validated with Pydantic."""
import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

Recurrence = Literal["none", "daily", "weekdays", "weekly", "biweekly", "monthly", "quarterly", "semiannual", "yearly"]
Category = Literal["task", "chore", "maintenance"]
Sticker = Literal["star", "smiley", "heart", "rainbow", "rocket", "trophy"]
Color = Literal["pink", "blue", "green", "yellow", "purple", "peach", "teal", "coral"]
Role = Literal["parent", "kid", "other"]


class _Trimmed(BaseModel):
    @field_validator("title", "name", check_fields=False)
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("can't be blank")
        return v


class MemberIn(_Trimmed):
    name: str = Field(min_length=1, max_length=50)
    role: Role = "kid"
    color: Color = "pink"
    emoji: str = Field(default="", max_length=8)


class EventIn(_Trimmed):
    title: str = Field(min_length=1, max_length=120)
    member_id: Optional[int] = None  # None = whole family
    start_date: dt.date
    start_time: Optional[dt.time] = None  # None = all day
    end_time: Optional[dt.time] = None
    location: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=2000)
    recurrence: Recurrence = "none"
    recurrence_end: Optional[dt.date] = None

    @model_validator(mode="after")
    def _check(self):
        if self.end_time and not self.start_time:
            raise ValueError("Add a start time before an end time")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after the start time")
        if self.recurrence == "none":
            self.recurrence_end = None
        elif self.recurrence_end and self.recurrence_end < self.start_date:
            raise ValueError("'Repeat until' must be on or after the start date")
        return self


class ChecklistItemIn(_Trimmed):
    id: Optional[int] = None  # existing item id; None = new item
    title: str = Field(min_length=1, max_length=120)


class TaskIn(_Trimmed):
    title: str = Field(min_length=1, max_length=120)
    member_id: Optional[int] = None  # None = everyone
    due_date: dt.date
    due_time: Optional[dt.time] = None
    notes: str = Field(default="", max_length=2000)
    recurrence: Recurrence = "none"
    recurrence_end: Optional[dt.date] = None
    items: list[ChecklistItemIn] = Field(default_factory=list, max_length=50)
    category: Category = "task"
    sticker: Sticker = "star"
    points: int = Field(default=1, ge=0, le=50)
    rotation: list[int] = Field(default_factory=list, max_length=20)  # chores: member ids taking turns
    rotate_every: Literal["day", "week"] = "week"

    @model_validator(mode="after")
    def _check(self):
        # de-duplicate rotation while keeping order
        self.rotation = list(dict.fromkeys(self.rotation))
        if len(self.rotation) == 1:
            self.member_id, self.rotation = self.rotation[0], []
        if self.rotation:
            self.member_id = self.rotation[0]
        if self.recurrence == "none":
            self.recurrence_end = None
        elif self.recurrence_end and self.recurrence_end < self.due_date:
            raise ValueError("'Repeat until' must be on or after the due date")
        return self


class ToggleIn(BaseModel):
    on_date: Optional[dt.date] = None


class PrizeIn(_Trimmed):
    title: str = Field(min_length=1, max_length=80)
    emoji: str = Field(default="🎁", max_length=8)
    cost: int = Field(default=10, ge=1, le=1000)


class RedeemIn(BaseModel):
    member_id: int
    prize_id: int


class BonusIn(BaseModel):
    member_id: int
    points: int = Field(default=1, ge=1, le=50)
    sticker: Sticker = "star"
    note: str = Field(default="", max_length=120)


class PinIn(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")
    current_pin: Optional[str] = None


class PinCheck(BaseModel):
    pin: str = Field(default="", max_length=8)


class StarterIn(BaseModel):
    keys: list[str] = Field(min_length=1, max_length=60)
    member_id: Optional[int] = None
    start_date: Optional[dt.date] = None


class ClearIn(BaseModel):
    what: Literal["activities", "rewards"]


class PhotoIn(BaseModel):
    data: str = Field(min_length=30, max_length=3_000_000)  # data:image/...;base64,...
