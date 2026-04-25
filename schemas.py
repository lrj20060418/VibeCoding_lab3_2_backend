from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class PlanCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=80)
    date: date
    budget: Optional[int] = Field(default=None, ge=0)
    people_count: Optional[int] = Field(default=None, ge=1, le=1000)
    preferences: Optional[str] = Field(default=None, max_length=2000)


class PlanUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=80)
    date: Optional[date] = None
    budget: Optional[int] = Field(default=None, ge=0)
    people_count: Optional[int] = Field(default=None, ge=1, le=1000)
    preferences: Optional[str] = Field(default=None, max_length=2000)


class PlanOut(BaseModel):
    id: str
    title: Optional[str]
    date: date
    budget: Optional[int]
    people_count: Optional[int]
    preferences: Optional[str]
    created_at: datetime
    updated_at: datetime


class PlanListResponse(BaseModel):
    plans: list[PlanOut]


class PlanResponse(BaseModel):
    plan: PlanOut

