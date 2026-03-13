from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, Request
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    age: int | None = Field(default=None, gt=0)
    is_subscribed: bool | None = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


ACCEPT_LANGUAGE_RE = re.compile(
    r"^[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})?(?:\s*,\s*[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})?(?:\s*;\s*q=0(?:\.\d{1,3})?|(?:\s*;\s*q=1(?:\.0{1,3})?)\s*)?)*$"
)


class CommonHeaders:
    def __init__(self, request: Request):
        user_agent = request.headers.get("User-Agent")
        accept_language = request.headers.get("Accept-Language")

        if not user_agent:
            raise HTTPException(status_code=400, detail='Missing required header "User-Agent"')
        if not accept_language:
            raise HTTPException(status_code=400, detail='Missing required header "Accept-Language"')
        if not ACCEPT_LANGUAGE_RE.match(accept_language):
            raise HTTPException(status_code=400, detail='Invalid "Accept-Language" format')

        self.user_agent = user_agent
        self.accept_language = accept_language


def get_common_headers(request: Request) -> CommonHeaders:
    return CommonHeaders(request)

