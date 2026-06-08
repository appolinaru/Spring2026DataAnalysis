"""Точка входа: демонстрация поиска по нормативам."""

from core.norms_process import search_norms


def main():
    """Главная функция: запрашивает описание здания и выводит нормативы."""
    print("=" * 50)
    print("Поиск по архитектурным нормативам")
    print("=" * 50)

    # Запрос от архитектора
    query = "двухэтажный монолитный жилой дом"
    print(f"\nЗапрос: {query}")
    print("-" * 50)

    # Поиск
    results = search_norms(query)

    # Вывод результатов
    if results:
        print(f"Найдено {len(results)} норматива:\n")
        for i, norm in enumerate(results, 1):
            print(f"{i}. [{norm['type']} {norm['number']}]")
            print(f"   {norm['text']}")
    else:
        print("Ничего не найдено.")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()