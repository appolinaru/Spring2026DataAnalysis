"""Pydantic-модель статической конфигурации."""

from pydantic import BaseModel, Field


class AppConfigModel(BaseModel):
    """Статическая конфигурация приложения."""

    app_name: str = Field(default="arch-rag-api", description="Название приложения")
    app_version: str = Field(default="1.0.0", description="Версия")
    app_description: str = Field(
        default="API для RAG-поиска по нормативам", description="Описание"
    )
    app_authors: list[str] = Field(default=["Polina"], description="Авторы")
    contact_email: str = Field(default="polina@example.com", description="Email")
    license_name: str = Field(default="MIT", description="Лицензия")

    model_config = {"frozen": True}
