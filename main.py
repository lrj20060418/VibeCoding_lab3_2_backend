from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from db import get_conn, init_db
from schemas import (
    ErrorResponse,
    PlanCreate,
    PlanListResponse,
    PlanOut,
    PlanResponse,
    PlanUpdate,
)

app = FastAPI(title="Lab 3-2 Backend", version="0.1.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plan_row_to_out(row) -> PlanOut:
    return PlanOut(
        id=row["id"],
        title=row["title"],
        date=row["date"],
        budget=row["budget"],
        people_count=row["people_count"],
        preferences=row["preferences"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def error(code: str, message: str, status_code: int) -> JSONResponse:
    body = ErrorResponse(error={"code": code, "message": message}).model_dump()
    return JSONResponse(status_code=status_code, content=body)


@app.post("/api/plans", response_model=PlanResponse)
def create_plan(payload: PlanCreate):
    plan_id = str(uuid4())
    now = _utc_now_iso()

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO plans (id, title, date, budget, people_count, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                payload.title,
                payload.date.isoformat(),
                payload.budget,
                payload.people_count,
                payload.preferences,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        return {"plan": _plan_row_to_out(row)}
    finally:
        conn.close()


@app.get("/api/plans", response_model=PlanListResponse)
def list_plans():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM plans ORDER BY updated_at DESC, created_at DESC"
        ).fetchall()
        return {"plans": [_plan_row_to_out(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/plans/{plan_id}", response_model=PlanResponse, responses={404: {"model": ErrorResponse}})
def get_plan(plan_id: str):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return error("PLAN_NOT_FOUND", "规划不存在", 404)
        return {"plan": _plan_row_to_out(row)}
    finally:
        conn.close()


@app.put("/api/plans/{plan_id}", response_model=PlanResponse, responses={404: {"model": ErrorResponse}})
def update_plan(plan_id: str, payload: PlanUpdate):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return error("PLAN_NOT_FOUND", "规划不存在", 404)

        # Partial update: only overwrite provided fields
        title = payload.title if payload.title is not None else row["title"]
        date = payload.date.isoformat() if payload.date is not None else row["date"]
        budget = payload.budget if payload.budget is not None else row["budget"]
        people_count = (
            payload.people_count
            if payload.people_count is not None
            else row["people_count"]
        )
        preferences = (
            payload.preferences
            if payload.preferences is not None
            else row["preferences"]
        )
        now = _utc_now_iso()

        conn.execute(
            """
            UPDATE plans
            SET title = ?, date = ?, budget = ?, people_count = ?, preferences = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, date, budget, people_count, preferences, now, plan_id),
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        return {"plan": _plan_row_to_out(updated)}
    finally:
        conn.close()

