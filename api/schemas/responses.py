"""Pydantic-модели ответов API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Ответ эндпоинта /health."""

    status: str


class MessageResponse(BaseModel):
    """Простой текстовый ответ."""

    message: str
