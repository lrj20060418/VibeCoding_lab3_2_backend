from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import get_conn, init_db
from schemas import PlaceCreate, PlaceOut, PlanCreate, PlanOut, PlanUpdate
from weather import WeatherKeyMissing, WeatherUpstreamError, get_live_weather_by_adcode

app = FastAPI(title="Lab 3-2 Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.on_event("startup")
def _startup():
    # Load local secrets from backend/.env (do not commit)
    load_dotenv()
    init_db()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@app.post("/api/plans", response_model=PlanOut)
def create_plan(payload: PlanCreate):
    plan_id = str(uuid4())
    now = _now_iso()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO plans (id, title, date, budget, people_count, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                payload.title,
                payload.date,
                payload.budget,
                payload.people_count,
                payload.preferences,
                now,
                now,
            ),
        )
        conn.commit()

        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()

    return PlanOut.model_validate(dict(row))


@app.get("/api/plans", response_model=list[PlanOut])
def list_plans():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM plans ORDER BY datetime(updated_at) DESC"
        ).fetchall()
    return [PlanOut.model_validate(dict(r)) for r in rows]


@app.get("/api/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanOut.model_validate(dict(row))


@app.put("/api/plans/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: str, payload: PlanUpdate):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Plan not found")

        current = dict(row)
        new_data = payload.model_dump(exclude_unset=True)
        merged = {**current, **new_data}
        merged["updated_at"] = _now_iso()

        conn.execute(
            """
            UPDATE plans
               SET title = ?,
                   date = ?,
                   budget = ?,
                   people_count = ?,
                   preferences = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                merged.get("title"),
                merged.get("date"),
                merged.get("budget"),
                merged.get("people_count"),
                merged.get("preferences"),
                merged.get("updated_at"),
                plan_id,
            ),
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()

    return PlanOut.model_validate(dict(updated))


@app.post("/api/plans/{plan_id}/places", response_model=PlaceOut)
def add_place(plan_id: str, payload: PlaceCreate):
    now = _now_iso()
    place_id = str(uuid4())

    with get_conn() as conn:
        plan = conn.execute("SELECT id FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        conn.execute(
            """
            INSERT INTO places (id, plan_id, name, address, lng, lat, adcode, note, sort_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                place_id,
                plan_id,
                payload.name,
                payload.address,
                payload.lng,
                payload.lat,
                payload.adcode,
                payload.note,
                payload.sort_index or 0,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()

    return PlaceOut.model_validate(dict(row))


@app.get("/api/plans/{plan_id}/places", response_model=list[PlaceOut])
def list_places(plan_id: str):
    with get_conn() as conn:
        plan = conn.execute("SELECT id FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        rows = conn.execute(
            """
            SELECT * FROM places
             WHERE plan_id = ?
             ORDER BY sort_index ASC, datetime(created_at) ASC
            """,
            (plan_id,),
        ).fetchall()

    return [PlaceOut.model_validate(dict(r)) for r in rows]


@app.delete("/api/plans/{plan_id}/places/{place_id}")
def delete_place(plan_id: str, place_id: str):
    with get_conn() as conn:
        plan = conn.execute("SELECT id FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        cur = conn.execute(
            "DELETE FROM places WHERE id = ? AND plan_id = ?",
            (place_id, plan_id),
        )
        conn.commit()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Place not found")
    return {"ok": True}


@app.get("/api/weather/live")
def weather_live(adcode: str):
    """
    统一天气服务（后端调用高德天气，前端不直连第三方）。
    """
    try:
        return {"weather": get_live_weather_by_adcode(adcode)}
    except WeatherKeyMissing as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except WeatherUpstreamError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.get("/api/plans/{plan_id}/weather/live")
def plan_weather_live(plan_id: str):
    """
    返回当前规划内地点的实时天气（按 place_id 聚合）。
    只对有 adcode 的地点查询；缺失 adcode 的地点会被跳过并返回原因。
    """
    with get_conn() as conn:
        plan = conn.execute("SELECT id FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        rows = conn.execute(
            "SELECT id, adcode FROM places WHERE plan_id = ? ORDER BY sort_index ASC, datetime(created_at) ASC",
            (plan_id,),
        ).fetchall()

    result: dict[str, object] = {}
    errors: dict[str, str] = {}
    for r in rows:
        place_id = r["id"]
        adcode = (r["adcode"] or "").strip()
        if not adcode:
            errors[place_id] = "Missing adcode"
            continue
        try:
            result[place_id] = get_live_weather_by_adcode(adcode)
        except Exception as e:
            errors[place_id] = str(e)

    return {"weathers": result, "errors": errors}

