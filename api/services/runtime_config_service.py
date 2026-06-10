"""Сервис runtime-конфигурации."""

from schemas.runtime_config import RuntimeConfigModel, RuntimeConfigUpdateModel


class RuntimeConfigService:
    """Управление runtime-настройками."""

    def __init__(self, initial_config: RuntimeConfigModel):
        self._config = initial_config.model_copy(deep=True)

    def get_config(self) -> RuntimeConfigModel:
        """Получить текущую конфигурацию."""
        return self._config

    def update_config(self, new_config: RuntimeConfigUpdateModel) -> RuntimeConfigModel:
        """Обновить конфигурацию."""
        self._config = RuntimeConfigModel(**new_config.model_dump())
        return self._config
