"""Runtime-конфигурация"""

from pydantic import BaseModel


class RuntimeSettings(BaseModel):
    log_level: str = "INFO"
    feature_flag: bool = False
    maintenance_mode: bool = False
    runtime_message: str = "Работа в штатном режиме"


class RuntimeConfigService:

    _instance = None
    _settings: RuntimeSettings = RuntimeSettings()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self) -> RuntimeSettings:
        return self._settings

    def update(self, new_settings: RuntimeSettings) -> RuntimeSettings:
        self._settings = new_settings
        return self._settings
