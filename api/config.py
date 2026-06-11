"""Статическая конфигурация приложения."""


class AppConfig:
    """применяется при старте."""

    def __init__(self):
        self.app_name = "arch-rag-api"
        self.app_version = "1.0.0"
        self.app_description = "API для RAG-поиска по архитектурным нормативам"
        self.app_authors = ["Polina"]
        self.contact_email = "polina@example.com"
        self.license_name = "MIT"

    def to_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_description": self.app_description,
            "app_authors": self.app_authors,
            "contact_email": self.contact_email,
            "license_name": self.license_name,
        }
