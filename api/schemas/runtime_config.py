"""Pydantic-модели runtime-конфигурации."""

from typing import Literal

from pydantic import BaseModel, Field


class RuntimeConfigModel(BaseModel):
    """Текущая runtime-конфигурация."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    feature_flag: bool = Field(default=False)
    maintenance_mode: bool = Field(default=False)
    runtime_message: str = Field(default="Приложение работает в штатном режиме")


class RuntimeConfigUpdateModel(BaseModel):
    """Модель для обновления runtime (тело PUT-запроса)."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    feature_flag: bool = Field(default=False)
    maintenance_mode: bool = Field(default=False)
    runtime_message: str = Field(default="Приложение работает в штатном режиме")
