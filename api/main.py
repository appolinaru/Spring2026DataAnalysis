"""Точка входа FastAPI приложения."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from init_dependencies import init_dependencies
from routes import config, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: инициализация зависимостей при старте."""
    deps = init_dependencies()
    app.state.dependencies = deps
    print(f"Dependencies initialized: {list(deps.keys())}")

    yield

    app.state.dependencies = None
    print("App is shutted down")


app = FastAPI(
    lifespan=lifespan,
    title=os.environ.get("APP_NAME", "arch-rag-api"),
    description=os.environ.get(
        "APP_DESCRIPTION", "API для RAG-поиска по архитектурным нормативам"
    ),
    version=os.environ.get("APP_VERSION", "1.0.0"),
)


@app.get("/")
def root():
    return {"message": "arch-rag API", "docs": "/docs"}


@app.get("/ping")
def ping_server():
    return "pong"


app.include_router(health.router)
app.include_router(config.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
