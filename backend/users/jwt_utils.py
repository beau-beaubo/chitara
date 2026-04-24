from __future__ import annotations

from datetime import datetime, timedelta

import jwt
from django.conf import settings


JWT_ALGORITHM = "HS256"
JWT_EXP_DAYS = 7


class JwtAuthError(ValueError):
    pass


def issue_jwt_for_user(user_id: int) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=JWT_EXP_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def parse_jwt_subject(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise JwtAuthError("invalid token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise JwtAuthError("invalid token subject")

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise JwtAuthError("invalid token subject") from exc
