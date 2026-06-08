"""Векторный поиск"""

import numpy as np
from loguru import logger

from arch_rag.core.norms import NormsSearcher
from arch_rag.exceptions import EmptyQueryError, NoResultsError


class VectorSearcher:
    """Векторный поиск по нормативам."""

    def __init__(self, norms: list = None):
        self.norms = norms if norms is not None else NormsSearcher().norms
        self.vocab = {}
        self.vectors = None
        self._build_vectors()

    def _tokenize(self, text: str) -> list[str]:
        """Простая токенизация."""
        text = text.lower()
        for char in ".,;:!?()[]{}\"'":
            text = text.replace(char, " ")
        return [w for w in text.split() if len(w) > 2]

    def _build_vectors(self) -> None:
        """Строит TF-IDF векторы."""
        if not self.norms:
            return

        # Собираем словарь
        all_texts = [n["text"] for n in self.norms]
        word_doc_count = {}

        for text in all_texts:
            words = set(self._tokenize(text))
            for w in words:
                word_doc_count[w] = word_doc_count.get(w, 0) + 1

        self.vocab = {w: i for i, w in enumerate(sorted(word_doc_count))}
        n_docs = len(all_texts)

        # TF-IDF матрица
        self.vectors = np.zeros((n_docs, len(self.vocab)))
        for i, text in enumerate(all_texts):
            words = self._tokenize(text)
            word_count = {}
            for w in words:
                word_count[w] = word_count.get(w, 0) + 1

            total = len(words)
            for w, count in word_count.items():
                if w not in self.vocab:
                    continue
                tf = count / total
                idf = np.log(n_docs / (word_doc_count[w] + 1)) + 1
                self.vectors[i, self.vocab[w]] = tf * idf

        # Нормализуем
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        self.vectors = self.vectors / (norms + 1e-10)

        logger.debug(f"Построено {n_docs} векторов размерности {len(self.vocab)}")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Векторный поиск."""
        query = query.strip()
        if not query:
            raise EmptyQueryError("Запрос не может быть пустым")

        if self.vectors is None:
            raise NoResultsError("База нормативов пуста")

        # Вектор запроса
        query_vec = np.zeros(len(self.vocab))
        words = self._tokenize(query)
        word_count = {}
        for w in words:
            word_count[w] = word_count.get(w, 0) + 1

        total = len(words)
        for w, count in word_count.items():
            if w not in self.vocab:
                continue
            tf = count / total
            idf = (
                np.log(
                    len(self.norms)
                    / (sum(1 for n in self.norms if w in n["text"].lower()) + 1)
                )
                + 1
            )
            query_vec[self.vocab[w]] = tf * idf

        # Нормализуем
        query_norm = np.linalg.norm(query_vec)
        query_vec = query_vec / (query_norm + 1e-10)

        # Cosine similarity
        scores = self.vectors @ query_vec

        # Топ-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                norm = self.norms[idx].copy()
                norm["vector_score"] = round(float(scores[idx]), 3)
                results.append(norm)

        if not results:
            raise NoResultsError(f"По запросу '{query}' ничего не найдено")

        logger.info(f"Векторный поиск: найдено {len(results)} результатов")
        return results
