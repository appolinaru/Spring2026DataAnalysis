"""Поиск по архитектурным нормативам."""

from loguru import logger

from arch_rag.exceptions import EmptyQueryError, NoResultsError
from arch_rag.utils.test_utils import normalize

_NORMS = [
    {
        "type": "СНиП",
        "number": "31-01-2003",
        "section": "4.2",
        "text": "Высота этажа в жилых помещениях должна быть не менее 2,5 м.",
    },
    {
        "type": "СНиП",
        "number": "31-01-2003",
        "section": "4.3",
        "text": "Жилые здания проектируют с высотой до 9 этажей включительно.",
    },
    {
        "type": "СП",
        "number": "54.13330.2016",
        "section": "5.2",
        "text": "Монолитные каркасные системы применяются до 25 этажей.",
    },
    {
        "type": "СП",
        "number": "54.13330.2016",
        "section": "5.3",
        "text": "Толщина монолитных стен не менее 180 мм.",
    },
    {
        "type": "ГОСТ",
        "number": "27751-2014",
        "section": "3.1",
        "text": "Коэффициент надежности для жилых зданий — 1,0.",
    },
]


class NormsSearcher:
    """Поиск по нормативам."""

    def __init__(self, norms: list[dict] = None):
        self.norms = norms if norms is not None else _NORMS
        logger.debug(f"Загружено {len(self.norms)} нормативов")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Ищет нормативы по запросу."""
        query = query.strip()
        if not query:
            raise EmptyQueryError("Запрос не может быть пустым")

        query_words = set(normalize(query))
        if not query_words:
            raise EmptyQueryError("Запрос не содержит слов")

        results = []
        for norm in self.norms:
            norm_words = set(normalize(norm["text"]))
            intersection = query_words & norm_words
            union = query_words | norm_words
            relevance = len(intersection) / len(union) if union else 0.0

            if relevance > 0:
                item = norm.copy()
                item["relevance"] = round(relevance, 3)
                results.append((relevance, item))

        results.sort(key=lambda x: x[0], reverse=True)
        filtered = [item for _, item in results[:top_k]]

        if not filtered:
            raise NoResultsError(f"По запросу '{query}' ничего не найдено")

        logger.info(f"Найдено {len(filtered)} результатов")
        return filtered
