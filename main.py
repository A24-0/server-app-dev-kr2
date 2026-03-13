from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from itsdangerous import BadSignature, Signer

from models import CommonHeaders, LoginRequest, UserCreate, get_common_headers

app = FastAPI()


@app.post("/create_user")
def create_user(user: UserCreate) -> UserCreate:
    return user


sample_product_1 = {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99}
sample_product_2 = {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99}
sample_product_3 = {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99}
sample_product_4 = {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99}
sample_product_5 = {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
sample_products = [sample_product_1, sample_product_2, sample_product_3, sample_product_4, sample_product_5]


@app.get("/product/{product_id}")
def get_product(product_id: int) -> dict[str, Any]:
    for p in sample_products:
        if p["product_id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/products/search")
def search_products(keyword: str, category: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    kw = keyword.strip().lower()
    cat = category.strip().lower() if category is not None else None
    out: list[dict[str, Any]] = []
    for p in sample_products:
        name = str(p.get("name", "")).lower()
        if kw and kw not in name:
            continue
        if cat is not None and str(p.get("category", "")).lower() != cat:
            continue
        out.append(p)
        if len(out) >= limit:
            break
    return out


VALID_USERNAME = "user123"
VALID_PASSWORD = "password123"

UNSIGNED_SESSIONS: dict[str, dict[str, Any]] = {}

SECRET_KEY = "dev-secret-key"
SESSION_COOKIE_NAME = "session_token"
SESSION_MAX_AGE_SECONDS = 300
SESSION_REFRESH_AFTER_SECONDS = 180


def _signer() -> Signer:
    return Signer(SECRET_KEY, sep=".", salt="session")


def _now_ts() -> int:
    return int(time.time())


def _validate_uuid(value: str) -> None:
    uuid.UUID(value)


def _make_signed_session_token(user_id: str, ts: int) -> str:
    value = f"{user_id}.{ts}"
    return _signer().sign(value).decode("utf-8")


def _verify_signed_session_token(token: str) -> tuple[str, int]:
    try:
        unsigned = _signer().unsign(token).decode("utf-8")
    except BadSignature as e:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"}) from e
    parts = unsigned.split(".")
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    user_id, ts_str = parts
    try:
        _validate_uuid(user_id)
        ts = int(ts_str)
    except Exception as e:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"}) from e
    now = _now_ts()
    if ts > now + 5:
        raise HTTPException(status_code=401, detail={"message": "Invalid session"})
    return user_id, ts


@app.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, Any]:
    if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
        response.status_code = 401
        return {"message": "Unauthorized"}

    user_id = str(uuid.uuid4())
    ts = _now_ts()
    token = _make_signed_session_token(user_id, ts)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        max_age=SESSION_MAX_AGE_SECONDS,
        samesite="lax",
    )

    unsigned_token = str(uuid.uuid4())
    UNSIGNED_SESSIONS[unsigned_token] = {"username": payload.username}
    response.set_cookie(
        key="session_token_v51",
        value=unsigned_token,
        httponly=True,
        secure=False,
        max_age=SESSION_MAX_AGE_SECONDS,
        samesite="lax",
    )

    return {"message": "OK"}


@app.get("/user")
def user(request: Request, response: Response) -> dict[str, Any]:
    token = request.cookies.get("session_token_v51")
    if token is None or token not in UNSIGNED_SESSIONS:
        response.status_code = 401
        return {"message": "Unauthorized"}
    return {"username": UNSIGNED_SESSIONS[token]["username"]}


@app.get("/profile")
def profile(request: Request, response: Response) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        response.status_code = 401
        return {"message": "Invalid session"}

    user_id, last_ts = _verify_signed_session_token(token)
    now = _now_ts()
    delta = now - last_ts

    if delta > SESSION_MAX_AGE_SECONDS:
        response.status_code = 401
        return {"message": "Session expired"}

    if SESSION_REFRESH_AFTER_SECONDS <= delta < SESSION_MAX_AGE_SECONDS:
        new_token = _make_signed_session_token(user_id, now)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=new_token,
            httponly=True,
            secure=False,
            max_age=SESSION_MAX_AGE_SECONDS,
            samesite="lax",
        )

    return {"user_id": user_id}


@app.get("/headers")
def headers(common: CommonHeaders = Depends(get_common_headers)) -> dict[str, str]:
    return {"User-Agent": common.user_agent, "Accept-Language": common.accept_language}


@app.get("/info")
def info(response: Response, common: CommonHeaders = Depends(get_common_headers)) -> dict[str, Any]:
    response.headers["X-Server-Time"] = datetime.now().isoformat(timespec="seconds")
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {"User-Agent": common.user_agent, "Accept-Language": common.accept_language},
    }

