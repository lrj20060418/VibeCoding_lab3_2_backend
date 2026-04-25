from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    date: str = Field(..., description="ISO 日期字符串，例如 2026-04-30")
    budget: Optional[int] = Field(default=None, ge=0)
    people_count: Optional[int] = Field(default=None, ge=1)
    preferences: Optional[str] = Field(default=None, max_length=2000)


class PlanUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    date: Optional[str] = None
    budget: Optional[int] = Field(default=None, ge=0)
    people_count: Optional[int] = Field(default=None, ge=1)
    preferences: Optional[str] = Field(default=None, max_length=2000)


class PlanOut(BaseModel):
    id: str
    title: Optional[str] = None
    date: str
    budget: Optional[int] = None
    people_count: Optional[int] = None
    preferences: Optional[str] = None
    created_at: str
    updated_at: str


class PlaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    lng: float
    lat: float
    adcode: Optional[str] = Field(default=None, max_length=32)
    note: Optional[str] = Field(default=None, max_length=500)
    sort_index: Optional[int] = Field(default=0)


class PlaceOut(BaseModel):
    id: str
    plan_id: str
    name: str
    address: Optional[str] = None
    lng: float
    lat: float
    adcode: Optional[str] = None
    note: Optional[str] = None
    sort_index: int
    created_at: str

