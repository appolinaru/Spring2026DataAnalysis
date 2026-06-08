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
