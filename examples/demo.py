"""Тестирование библиотеки arch_rag."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from arch_rag import ConceptBuilder, EmptyQueryError, NormsSearcher, VectorSearcher

# === Тест 1: Поиск по ключевым словам ===
print("=== Тест 1: NormsSearcher ===")
searcher = NormsSearcher()
results = searcher.search("двухэтажный монолитный дом", top_k=3)
for r in results:
    print(
        f"[{r['type']} {r['number']}] {r['text'][:50]}... (релевантность: {r['relevance']})"
    )

# === Тест 2: Векторный поиск ===
print("\n=== Тест 2: VectorSearcher ===")
vsearcher = VectorSearcher()
vresults = vsearcher.search("высота потолков в жилом доме", top_k=2)
for r in vresults:
    print(f"[{r['type']}] {r['text'][:50]}... (score: {r['vector_score']})")

# === Тест 3: Сборка концепта ===
print("\n=== Тест 3: ConceptBuilder ===")
builder = ConceptBuilder()
concept = builder.build("Двухэтажный монолитный жилой дом")
print(concept["text"])

# === Тест 4: Исключения ===
print("\n=== Тест 4: Исключения ===")
try:
    searcher.search("")
except EmptyQueryError as e:
    print(f"Поймали ошибку: {e}")

print("\n✅ Все тесты пройдены!")
