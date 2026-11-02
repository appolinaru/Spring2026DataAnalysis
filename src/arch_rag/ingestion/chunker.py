"""Структурно-ориентированная нарезка сконвертированного документа на нормы.

Модуль превращает результат :func:`arch_rag.ingestion.docling_converter.convert_pdf`
в список словарей, совместимых со схемой ``NormsSearcher``/``VectorSearcher``:

    {"type": "СП", "number": "54.13330.2016", "section": "4.2",
     "text": "...", "pages": [7, 8]}

Логика:
1. Обход элементов документа (заголовки разделов, нумерованные пункты,
   таблицы) в порядке чтения.
2. Фильтрация «мебели»: колонтитулы, строки оглавления с отточием,
   служебные пометки («независимая экспертиза», «Издание официальное»).
3. Накопление текста текущего пункта; новый заголовок/пункт — граница чанка.
4. Очень длинные пункты режутся по предложениям до ``max_chars``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Union

from loguru import logger

from arch_rag.exceptions import DocumentLoadError
from arch_rag.ingestion.docling_converter import DOCLING_FORMAT, FORMAT_KEY, PYPDF_FORMAT

PathLike = Union[str, Path]

# --- Регулярные выражения для структуры российских нормативов -----------------

# Тип и номер документа: "СП 54.13330.2016", "СНиП 31-01-2003", "ГОСТ 27751-2014"
DOC_RE = re.compile(
    r"(?P<type>СП|СНиП|ГОСТ|R\s*51584|МДС)\s*"
    r"(?P<number>\d[\w./\-]*\d(?:\.\d{2,4})?)",
    re.UNICODE,
)

# Номер раздела/пункта в начале строки: "4.2", "5.2.14", "п. 4.3".
# Ограничение {0,2} защищает от ложных срабатываний на датах ("3 декабря 2016 г.")
# и ссылках на другие нормативы ("СП 1.13130.2009").
CLAUSE_RE = re.compile(
    r"^((?:п\.|пп\.)\s*)?(?P<num>\d+(?:\.\d+){0,2})(?![\d.])(?P<sep>\s+[^\s]|\s*$)(?P<rest>.*)$",
    re.DOTALL,
)
APPENDIX_RE = re.compile(r"^прил(?:ожение)?\s*(?P<num>[A-ZА-ЯЁ]|\d+)\b", re.IGNORECASE | re.DOTALL)

# Ссылки на другие нормативы — не являются пунктами текущего документа
DOC_REF_RES = [
    re.compile(r"^(СП|СНиП|ГОСТ|R\s*51584|МДС|РД)\s+\d"),
    re.compile(r"\s\d{4}\.\d{2,4}\b"),  # ".2016", ".2009" — год издания в номере
]

# Настоящий пункт: номер + кириллическое слово сразу (или после "п." )
_REAL_CLAUSE_RE = re.compile(
    r"^((?:п\.|пп\.)\s*)?\d+(?:\.\d+){0,2}(?![\d.])\s*[А-Яа-яЁё]"
)


def _looks_like_real_clause(text: str) -> bool:
    """Отсекает ложные границы: годы ('2016 г.'), перечисления предисловия
    ('1 ИСПОЛНИТЕЛЬ — ...'), ссылки ('СП 4.13130.2013 ...')."""
    if not _REAL_CLAUSE_RE.match(text):
        return False
    m = CLAUSE_RE.match(text)
    if not m:
        return False
    num = m.group("num")
    rest = m.group("rest").strip()
    # Служебные поля предисловия: "1 ИСПОЛНИТЕЛЬ — ...", "4 УТВЕРЖДЕН приказом..."
    if FRONTMATTER_KEYWORD_RE.match(rest):
        return False
    # Год: "2016 г. N 883/пр" — номер длинный и за ним сокращение года
    if len(num) >= 4 and re.match(r"^(г\.|года|год)\b", rest):
        return False
    # Ссылка на другой документ внутри строки: "4 СП 15.13330.2012 ..."
    if DOC_REF_RES[0].match(rest):
        return False
    return True

# Колонтитулы и прочая «мебель»
FURNITURE_RES = [
    re.compile(r"^СП\s+\d[\d./\-]+\s*$"),          # повторяющийся хедер "СП 54.13330.2016"
    re.compile(r"^СНиП\s+\d[\d./\-]+\s*$"),
    re.compile(r"^ГОСТ\s+\d[\d.-]+\s*$"),
    re.compile(r"^\d{1,3}$"),                       # номер страницы
    re.compile(r"^(издание официальное|независимая экспертиза|предисловие|"
               r"содержание|введение|application|abstract)\b.*$", re.IGNORECASE),
    re.compile(r"^[.,·•\s]{6,}$"),                  # чисто точечная строка
    re.compile(r"\.{5,}\s*\d{1,3}$"),               # строка оглавления "Раздел 4 ..... 12"
    re.compile(r"^https?://|\S+@\S+\.\w{2,}$"),     # URL/e-mail из выходных данных
    re.compile(r"^\W*(москва|стандартинформ)\W*$", re.IGNORECASE),
]

# Строки предисловий/выходных данных с нумерованными служебными полями:
# "1 ИСПОЛНИТЕЛЬ — ...", "4 УТВЕРЖДЕН приказом ..." — не являются пунктами норм.
FRONTMATTER_KEYWORD_RE = re.compile(
    r"^(ИСПОЛНИТЕЛЬ|ВНЕСЕН|ПОДГОТОВЛЕН|УТВЕРЖДЕН|ВВЕДЕН|РАЗРАБОТАН|СОГЛАСОВАН)\b",
    re.IGNORECASE | re.DOTALL,
)

# Табличные/перечислительные артефакты, которые не являются нормами
BULLET_RE = re.compile(r"^[-–—▪•o]\s+")

MIN_CHUNK_CHARS = 40
MAX_CHUNK_CHARS = 900


def _join_wrapped_words(items):
    """Склеивает строки, оборванные на середине слова (перенос через дефис)."""
    out = []
    for label, text, page in items:
        prev = out[-1] if out else None
        if prev and prev[1].endswith("-"):
            merged = prev[1][:-1] + text
            out[-1] = (prev[0], merged, prev[2])
            continue
        out.append((label, text, page))
    return out


def _word_wrap(prev_text: str, next_text: str) -> bool:
    """True, если next_text — продолжение prev_text, разорванного без дефиса.

    Признаки: предыдущая строка кончается строчной буквой, следующая
    начинается со строчной, при этом следующая не является пунктом/заголовком.
    """
    if not prev_text or not next_text:
        return False
    a, b = prev_text[-1], next_text[0]
    if not (a.islower() and a.isalpha() and b.islower() and b.isalpha()):
        return False
    # Не склеиваем, если следующая строка похожа на самостоятельный пункт
    if re.match(r"^(?:\d+(?:\.\d+){0,2})\s", next_text):
        return False
    return True


def _is_furniture(text: str) -> bool:
    """True, если строку следует выбросить (колонтитул, оглавление, мусор)."""
    t = text.strip()
    if len(t) < 2:
        return True
    return any(rx.match(t) for rx in FURNITURE_RES)


def _detect_doc_meta(texts: Iterable[str]) -> tuple[str, str]:
    """Определяет (type, number) документа по первым строкам."""
    for t in texts:
        m = DOC_RE.search(t.replace("\u00ad", ""))
        if m and len(m.group("number")) >= 3:
            return m.group("type"), m.group("number")
    return "СП", "unknown"


def _split_long(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Режет длинный пункт по предложениям, не превышая max_chars."""
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts, buf = [], ""
    for s in sentences:
        if buf and len(buf) + len(s) + 1 > max_chars:
            parts.append(buf)
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        parts.append(buf)
    return parts


class _ChunkAccumulator:
    """Накапливает строки текущего пункта; flush при смене границы."""

    def __init__(self, doc_type: str, doc_number: str):
        self.doc_type = doc_type
        self.doc_number = doc_number
        self.section: str | None = None
        self.lines: list[str] = []
        self.pages: set[int] = set()

    def boundary(self, section: str | None) -> list[dict]:
        out = self.flush()
        self.section = section
        return out

    def add(self, text: str, page: int | None) -> None:
        self.lines.append(text)
        if page:
            self.pages.add(page)

    def flush(self) -> list[dict]:
        if not self.lines:
            return []
        body = " ".join(self.lines).strip()
        self.lines = []
        pages = sorted(self.pages)
        self.pages = set()
        if len(body) < MIN_CHUNK_CHARS or _is_furniture(body):
            return []
        chunks = []
        for piece in _split_long(body):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                {
                    "type": self.doc_type,
                    "number": self.doc_number,
                    "section": self.section or "",
                    "text": piece,
                    "pages": pages,
                }
            )
        return chunks


def _walk_docling_items(items: list[dict], export: dict, depth: int = 0) -> list:
    """Обходит дерево элементов, возвращая [(label, text, page_no), ...]."""
    out = []
    for it in items:
        label = it.get("label", "")
        text = (it.get("text") or "").replace("\u00ad", "").strip()
        prov = it.get("prov") or []
        page = prov[0].get("page_no") if prov else None

        if label == "group" or "items" in it:
            children = it.get("items") or []
            out.extend(_walk_docling_items(children, export, depth + 1))
            continue

        if label == "table":
            table_text = _table_to_text(it)
            if table_text:
                out.append(("table", table_text, page))
            continue

        if text:
            out.append((label, text, page))
    return out


def _table_to_text(table_item: dict) -> str:
    """Таблица → плоский текст (для поиска формулировок внутри таблиц)."""
    data = table_item.get("data") or {}
    cells = data.get("cells") or []
    tfs = table_item.get("export") or {}
    md = tfs.get("md_text") or tfs.get("text") or ""
    if md:
        return re.sub(r"\s+", " ", md).strip()
    parts = [str(c.get("text", "")).strip() for c in cells if c.get("text")]
    return "; ".join(parts)


def chunk_document(export: dict, max_chunk_chars: int = MAX_CHUNK_CHARS) -> list[dict]:
    """Главная точка входа: dict-документ (docling или pypdf-fallback) → нормы."""
    fmt = export.get(FORMAT_KEY)
    if fmt == PYPDF_FORMAT:
        raw_items = [
            ("text", it["text"], (it.get("prov") or [{}])[0].get("page_no"))
            for it in export.get("items", [])
        ]
    elif fmt == DOCLING_FORMAT:
        raw_items = _walk_docling_items(export.get("body", {}).get("items", []), export)
    else:
        raise DocumentLoadError(
            f"Неизвестный формат конвертации: {fmt!r}. Используйте convert_pdf()."
        )

    if not raw_items:
        logger.warning("Документ пуст после конвертации")
        return []

    # Нормализация: склеиваем строки, оборванные на середине слова.
    # Варианты переноса в PDF: "про\xad" (soft hyphen), "про-" (дефис),
    # "конструк\nциями" (прямая разбивка слова без разделителя).
    def _norm(t: str) -> tuple[str, bool]:
        t = t.replace("\u00ad", "").strip()
        if t.endswith("-"):
            return t[:-1], True
        return t, False

    joined: list[list] = []
    for label, text, page in raw_items:
        clean, had_hyphen = _norm(text)
        if not clean:
            continue
        if joined:
            prev = joined[-1]
            merge = had_hyphen or prev[3] or _word_wrap(prev[1], clean)
            if merge and prev[2] == page:
                sep = "" if (had_hyphen or prev[3]) else " "
                prev[0] = f"{prev[0]}{sep}{clean}"
                prev[3] = had_hyphen or prev[3]
                continue
        joined.append([clean, 0, page, had_hyphen])
    raw_items = [(j[0], j[1], j[2]) for j in joined]

    head_texts = [t for _, t, _ in raw_items[:30]]
    doc_type, doc_number = _detect_doc_meta(head_texts)
    logger.info(f"Документ определён как: {doc_type} {doc_number}")

    acc = _ChunkAccumulator(doc_type, doc_number)
    norms: list[dict] = []
    current_section: str | None = None

    for label, text, page in raw_items:
        clean = text.strip()
        if _is_furniture(clean):
            continue

        is_title = label.startswith("title") or label == "section_header" or label == "header"
        m_clause = CLAUSE_RE.match(clean) if _looks_like_real_clause(clean) else None
        m_app = APPENDIX_RE.match(clean)

        new_section = current_section
        if is_title and m_app:
            new_section = f"Приложение {m_app.group('num')}"
        elif is_title and m_clause:
            new_section = m_clause.group("num")
        elif (
            not is_title
            and m_clause
            and (current_section is None or _starts_new_clause(m_clause, current_section))
        ):
            new_section = m_clause.group("num")
            # Инлайн-нумерация: сам номер выносим из тела пункта
            clean = f"{m_clause.group('num')} {m_clause.group('rest').strip()}".strip()

        if new_section != current_section:
            norms.extend(acc.boundary(new_section))
            current_section = new_section

        # Строки перечислений склеиваем с текущим пунктом, остальные — как новые предложения
        body = BULLET_RE.sub("", clean)
        if len(body) < 3:
            continue
        acc.add(body, page)

    norms.extend(acc.flush())

    # Финальная подчистка лимитом
    for n in norms:
        n_text = n["text"]
        if len(n_text) > max_chunk_chars:
            idx = norms.index(n)
            repl = [{**n, "text": p} for p in _split_long(n_text, max_chunk_chars)]
            norms[idx : idx + 1] = repl

    logger.info(f"Сформировано {len(norms)} норм из документа {doc_type} {doc_number}")
    return norms


def _is_doc_ref(text: str) -> bool:
    """True, если строка ссылается на другой норматив (не пункт текущего)."""
    return any(rx.search(text) for rx in DOC_REF_RES)


def _starts_new_clause(m: re.Match, current: str) -> bool:
    """Новый ли это пункт (а не продолжение «5.2.1 ...» внутри п. 5.2)."""
    num = m.group("num")
    return num != current and not num.startswith(current + ".")


def save_norms_json(norms: list[dict], path: PathLike) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(norms, fh, ensure_ascii=False, indent=2)
    logger.info(f"Нормы сохранены: {path} ({len(norms)} шт.)")
    return path


def load_norms_json(path: PathLike) -> list[dict]:
    path = Path(path)
    if not path.exists():
        raise DocumentLoadError(f"Файл норм не найден: {path}")
    with path.open(encoding="utf-8") as fh:
        norms = json.load(fh)
    logger.info(f"Загружены нормы из {path.name}: {len(norms)} шт.")
    return norms
