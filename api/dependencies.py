"""Функции-провайдеры зависимостей для FastAPI Depends."""

from fastapi import Request
from schemas.app_config import AppConfigModel
from services.runtime_config_service import RuntimeConfigService


def get_dependencies(request: Request) -> dict:
    """Получить контейнер зависимостей из состояния приложения."""
    return request.app.state.dependencies


def get_app_config(request: Request) -> AppConfigModel:
    """Dependency-провайдер: статическая конфигурация приложения."""
    deps = get_dependencies(request)
    return deps.get_dependency("app_config")


def get_runtime_service(request: Request) -> RuntimeConfigService:
    """Dependency-провайдер: сервис runtime-конфигурации."""
    deps = get_dependencies(request)
    return deps.get_dependency("runtime_service")
