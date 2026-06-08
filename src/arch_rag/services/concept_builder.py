"""Сервис сборки архитектурной концепции из нормативов."""

import re
from typing import Optional

from arch_rag.core.norms import NormsSearcher
from arch_rag.core.vector_search import VectorSearcher
from arch_rag.exceptions import NoResultsError


class ConceptBuilder:
    """
    Строит архитектурную концепцию на основе нормативов.

    Пример:
        >>> builder = ConceptBuilder()
        >>> concept = builder.build("двухэтажный монолитный дом")
        >>> print(concept["text"])
    """

    def __init__(self, use_vector: bool = True):
        self.searcher = VectorSearcher() if use_vector else NormsSearcher()

    def build(self, description: str) -> dict:
        """
        Собирает концепцию из нормативов.

        Returns:
            dict с полями: text, norms, params
        """
        try:
            norms = self.searcher.search(description, top_k=5)
        except NoResultsError:
            norms = []

        # Извлекаем параметры из описания
        params = self._extract_params(description)

        # Формируем текст концепции
        text = self._build_text(description, norms, params)

        return {
            "text": text,
            "norms": norms,
            "params": params,
        }

    def _extract_params(self, description: str) -> dict:
        """Извлекает параметры из описания."""
        params = {"floors": None, "structure": None, "area": None}

        # Ищем цифру + "этаж" или слово "двухэтажный", "трёхэтажный"
        text_lower = description.lower()

        # Числовая этажность: "2 этажа", "двухэтажный"
        floor_words = {
            "одно": 1,
            "двух": 2,
            "трёх": 3,
            "трех": 3,
            "четырёх": 4,
            "четырех": 4,
            "пяти": 5,
            "шести": 6,
            "семи": 7,
            "восьми": 8,
            "девяти": 9,
        }

        # Проверяем словесную этажность
        for word, num in floor_words.items():
            if word in text_lower:
                params["floors"] = num
                break

        # Если не нашли словом, ищем цифру
        if params["floors"] is None:
            match = re.search(r"(\d+)[-\s]?этаж", text_lower)
            if match:
                params["floors"] = int(match.group(1))

        # Конструкция
        structures = {
            "монолит": "монолитный каркас",
            "кирпич": "кирпичная кладка",
            "каркас": "стальной каркас",
            "панель": "панельный",
            "дерев": "деревянный",
        }
        for key, val in structures.items():
            if key in text_lower:
                params["structure"] = val
                break

        # Площадь
        area_match = re.search(r"(\d+)\s*м²?", text_lower)
        if area_match:
            params["area"] = int(area_match.group(1))

        return params

    def _build_text(self, description: str, norms: list, params: dict) -> str:
        """Формирует текстовое описание концепции."""
        lines = [
            f"## Архитектурная концепция",
            f"",
            f"**Исходное описание:** {description}",
            f"",
            f"**Параметры:**",
            f"- Этажность: {params['floors'] or 'не указана'}",
            f"- Конструкция: {params['structure'] or 'не указана'}",
            f"- Площадь: {params['area'] or 'не указана'} м²",
            f"",
            f"**Применённые нормативы:**",
        ]

        for norm in norms:
            lines.append(f"- [{norm['type']} {norm['number']}] {norm['text']}")

        return "\n".join(lines)
