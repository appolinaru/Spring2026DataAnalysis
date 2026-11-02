"""Пользовательские исключения."""


class ArchRAGError(Exception):
    """Базовое исключение."""

    pass


class EmptyQueryError(ArchRAGError):
    """Пустой запрос."""

    pass


class NoResultsError(ArchRAGError):
    """Ничего не найдено."""

    pass


class ConversionError(ArchRAGError):
    """Ошибка конвертации PDF-документа."""

    pass


class DocumentLoadError(ConversionError):
    """Не удалось загрузить/прочитать документ."""

    pass
