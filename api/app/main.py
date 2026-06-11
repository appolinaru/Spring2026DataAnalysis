"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI

from app.territories.router import router as territories_router

app = FastAPI(
    title="Urban Spatial Database API",
    description="CRUD-сервис для городских территорий и показателей",
    version="1.0.0",
)

app.include_router(territories_router)


@app.get("/health")
def health_check():
    """Проверка работоспособности приложения."""
    return {"status": "ok"}