"""Эндпоинт проверки работоспособности."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Проверка работоспособности приложения."""
    return {"status": "ok"}
