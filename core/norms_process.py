"""Поиск по архитектурным нормативам (СНиП, СП, ГОСТ)."""


NORMS = [
    {
        "type": "СНиП",
        "number": "31-01-2003",
        "text": "Высота этажа в жилых помещениях должна быть не менее 2,5 м."
    },
    {
        "type": "СНиП",
        "number": "31-01-2003",
        "text": "Жилые здания проектируют с высотой до 9 этажей включительно."
    },
    {
        "type": "СП",
        "number": "54.13330.2016",
        "text": "Монолитные каркасные системы применяются до 25 этажей."
    },
    {
        "type": "СП",
        "number": "54.13330.2016",
        "text": "Толщина монолитных стен не менее 180 мм."
    },
    {
        "type": "ГОСТ",
        "number": "27751-2014",
        "text": "Коэффициент надежности для жилых зданий — 1,0."
    }
]


def _normalize(word: str) -> str:
    """Упрощённая нормализация: убираем окончания."""
    endings = ("ый", "ий", "ой", "ая", "ое", "ые", "ие", "ого", "ому",
               "ых", "им", "ыми", "ий", "его", "ему", "их", "ими",
               "ать", "ять", "уть", "ить", "еть", "ать", "ять",
               "ов", "ев", "ам", "ами", "ах",
               "ть", "ся", "сь", "но", "на", "ые", "ой", "ом")
    for end in endings:
        if word.endswith(end):
            return word[:-len(end)]
    return word


def search_norms(query: str) -> list:
    """Ищет нормативы по ключевым словам из запроса."""
    query_words = [_normalize(w) for w in query.lower().split() if len(w) > 2]
    results = []

    for norm in NORMS:
        norm_text = norm["text"].lower()
        norm_words = [_normalize(w) for w in norm_text.split() if len(w) > 2]

        matches = 0
        for qw in query_words:
            for nw in norm_words:
                if qw in nw or nw in qw:
                    matches += 1
                    break

        if matches > 0:
            results.append((matches, norm))

    results.sort(key=lambda x: x[0], reverse=True)

    return [norm for _, norm in results]