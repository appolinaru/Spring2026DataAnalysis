"""Эндпоинты конфигурации."""

from config import AppConfig
from fastapi import APIRouter
from services.runtime_config import RuntimeConfigService, RuntimeSettings

router = APIRouter()


@router.get("/config/app")
def get_app_config():
    """Статическая конфигурация приложения."""
    config = AppConfig()
    return config.to_dict()


@router.get("/config/runtime")
def get_runtime_config():
    """Текущие runtime-настройки."""
    service = RuntimeConfigService()
    return service.get().model_dump()


@router.put("/config/runtime")
def update_runtime_config(settings: RuntimeSettings):
    """Обновление runtime-настроек."""
    service = RuntimeConfigService()
    updated = service.update(settings)
    return updated.model_dump()
