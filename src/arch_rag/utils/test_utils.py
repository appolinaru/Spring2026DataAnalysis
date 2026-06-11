"""Утилиты обработки текста."""


def normalize(text: str) -> list[str]:
    """Разбивает текст на слова, убирает окончания."""
    text = text.lower().strip()
    for char in ".,;:!?()[]{}\"'":
        text = text.replace(char, " ")

    words = text.split()
    result = []

    for word in words:
        if len(word) <= 3:
            result.append(word)
            continue

        endings = (
            "ый",
            "ий",
            "ой",
            "ая",
            "ое",
            "ые",
            "ие",
            "ого",
            "ому",
            "ых",
            "им",
            "ыми",
            "его",
            "ему",
            "их",
            "ими",
            "ов",
            "ев",
            "ам",
            "ами",
            "ах",
            "ть",
            "ся",
            "сь",
            "но",
            "на",
            "ом",
            "ешь",
            "ете",
            "ет",
            "ут",
            "ют",
            "ем",
            "им",
        )
        for end in endings:
            if word.endswith(end):
                word = word[: -len(end)]
                break

        result.append(word)

    return result
