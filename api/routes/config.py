"""Эндпоинты конфигурации."""

from dependencies import get_app_config, get_runtime_service
from fastapi import APIRouter, Depends
from schemas.app_config import AppConfigModel
from schemas.runtime_config import RuntimeConfigModel, RuntimeConfigUpdateModel
from services.runtime_config_service import RuntimeConfigService

router = APIRouter(tags=["configuration"])


@router.get("/config/app", response_model=AppConfigModel)
def get_app_config_endpoint(
    config: AppConfigModel = Depends(get_app_config),
) -> AppConfigModel:
    """Статическая конфигурация приложения."""
    return config


@router.get("/config/runtime", response_model=RuntimeConfigModel)
def get_runtime_config(
    service: RuntimeConfigService = Depends(get_runtime_service),
) -> RuntimeConfigModel:
    """Текущие runtime-настройки."""
    return service.get_config()


@router.put("/config/runtime", response_model=RuntimeConfigModel)
def update_runtime_config(
    new_settings: RuntimeConfigUpdateModel,
    service: RuntimeConfigService = Depends(get_runtime_service),
) -> RuntimeConfigModel:
    """Обновление runtime-настроек."""
    return service.update_config(new_settings)
