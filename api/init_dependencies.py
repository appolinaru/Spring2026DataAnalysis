"""Инициализация кастомного словаря зависимостей."""

from typing import Any


class DependenciesDict(dict):
    """Кастомный словарь зависимостей с безопасным получением по ключу."""

    def get_dependency(self, key: str) -> Any:
        """Безопасно получить зависимость по ключу."""
        if key not in self:
            raise KeyError(
                f"Зависимость '{key}' не найдена. " f"Доступные: {list(self.keys())}"
            )
        return self[key]


def init_dependencies() -> DependenciesDict:
    """Создать и вернуть контейнер зависимостей."""
    from schemas.app_config import AppConfigModel
    from schemas.runtime_config import RuntimeConfigModel
    from services.runtime_config_service import RuntimeConfigService

    app_config = AppConfigModel(
        app_name="arch-rag-api",
        app_version="1.0.0",
        app_description="API для RAG-поиска по архитектурным нормативам",
        app_authors=["Polina"],
        contact_email="polina@example.com",
        license_name="MIT",
    )

    runtime_config = RuntimeConfigModel(
        log_level="INFO",
        feature_flag=False,
        maintenance_mode=False,
        runtime_message="Работа в штатном режиме",
    )

    runtime_service = RuntimeConfigService(initial_config=runtime_config)

    return DependenciesDict(
        {
            "app_config": app_config,
            "runtime_service": runtime_service,
        }
    )
