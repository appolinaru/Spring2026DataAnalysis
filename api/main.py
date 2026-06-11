"""Точка входа FastAPI приложения."""

from config import AppConfig
from fastapi import FastAPI
from routes import config, health

app_config = AppConfig()

app = FastAPI(
    title=app_config.app_name,
    version=app_config.app_version,
    description=app_config.app_description,
)


app.include_router(health.router)
app.include_router(config.router)


@app.get("/")
def root():
    return {"message": "arch-rag API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
