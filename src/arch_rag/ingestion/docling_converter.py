"""Конвертация PDF нормативных документов через Docling.

Модуль изолирует зависимость от ``docling``: точная конвертация требует
именно его (структурные метки, нумерация пунктов, таблицы, ссылки на
страницы). Лёгкий pypdf-fallback даёт низкое качество чанкинга по
сравнению с Docling и поэтому **не включается автоматически** — его нужно
явно запросить флагом ``allow_pypdf_fallback=True`` (или ``--allow-fallback``
в CLI), понимая, что границы пунктов будут хуже.

Результат работы — сериализованный ``DoclingDocument`` (JSON), который
далее разбирается модулем :mod:`arch_rag.ingestion.chunker`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from loguru import logger

from arch_rag.exceptions import ConversionError, DocumentLoadError

PathLike = Union[str, Path]

# Ключ-маркер формата: по нему chunker понимает, чем именно сконвертирован файл.
FORMAT_KEY = "_arch_rag_format"
DOCLING_FORMAT = "docling"
PYPDF_FORMAT = "pypdf"


def is_docling_available() -> bool:
    """Проверяет, установлен ли docling."""
    try:
        import docling  # noqa: F401
    except ImportError:
        return False
    return True


def _docling_options():
    """Опции конвейера Docling, безопасные для CPU-сред с ограниченной памятью.

    Отключены OCR и распознавание табличной структуры — это самые
    «прожорливые» модели (по сотен МБ–ГБ каждая). Для текстовых PDF
    СП/СНиП/ГОСТ они не нужны: слой текста извлекается напрямую.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False
    options.do_table_structure = False
    options.generate_page_images = False
    options.generate_picture_images = False

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
        }
    )


def _convert_with_docling(pdf_path: Path, max_pages: int | None) -> dict:
    """Конвертирует PDF Docling-ом и возвращает документ как dict (JSON-safe)."""
    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.datamodel.document import ConversionResult  # noqa: F401
    except ImportError as exc:  # pragma: no cover - версия docling
        raise ConversionError(f"Не удалось импортировать docling: {exc}") from exc

    converter = _docling_options()

    page_range = f"1-{max_pages}" if max_pages else None
    logger.info(
        f"Docling: конвертация {pdf_path.name}"
        + (f" (страницы {page_range})" if page_range else "")
    )

    result = converter.convert(
        pdf_path,
        page_range=page_range,
        raises_on_error=False,
    )

    if result.status.value.lower() not in ("success", "partial_success"):
        err_items = [str(e) for e in (result.errors or [])]
        raise ConversionError(
            f"Docling не смог сконвертировать {pdf_path.name}: "
            + "; ".join(err_items[:5])
        )

    doc = result.document
    export = doc.export_to_dict()
    export[FORMAT_KEY] = DOCLING_FORMAT
    logger.info(
        f"Docling: получено элементов: text={len(export.get('texts', []))}, "
        f"tables={len(export.get('tables', []))}, pages={len(export.get('pages', {}))}"
    )
    return export


def _convert_with_pypdf(pdf_path: Path, max_pages: int | None) -> dict:
    """Fallback: извлечение текста страниц через pypdf в формат, совместимый
    с ``iterate_items``-подобным разбором (см. chunker.chunks_from_fallback)."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentLoadError(
            "Для fallback-конвертации установите pypdf: pip install pypdf"
        ) from exc

    reader = PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    limit = min(max_pages, n_pages) if max_pages else n_pages
    logger.warning(
        f"Fallback (pypdf): извлечение текста из {pdf_path.name}, страниц: {limit}"
    )

    items = []
    for i in range(limit):
        page_text = reader.pages[i].extract_text() or ""
        for line_no, line in enumerate(page_text.splitlines(), start=1):
            line = line.replace("\u00ad", "").strip()
            if not line:
                continue
            items.append(
                {
                    "label": "text",
                    "text": line,
                    "prov": [{"page_no": i + 1}],
                    "$ref": None,
                    "_line": line_no,
                }
            )
    return {FORMAT_KEY: PYPDF_FORMAT, "items": items, "n_pages": n_pages}


def _convert_with_pypdf(pdf_path: Path, max_pages: int | None) -> dict:
    """Fallback-извлечение текста через pypdf (линейные строки страниц).

    Качество чанкинга при этом хуже, чем у Docling: теряются структурные
    метки заголовков/таблиц. Используется только при явном запросе
    (``allow_pypdf_fallback=True``), например для черновой индексации в
    среде без docling/достаточной памяти.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentLoadError(
            "Для fallback-конвертации установите pypdf: pip install pypdf"
        ) from exc

    reader = PdfReader(str(pdf_path))
    n_pages = len(reader.pages)
    limit = min(max_pages, n_pages) if max_pages else n_pages
    logger.warning(
        f"Fallback (pypdf): извлечение текста из {pdf_path.name}, страниц: {limit}. "
        "Внимание: качество чанкинга ниже, чем у Docling."
    )

    items = []
    for i in range(limit):
        page_text = reader.pages[i].extract_text() or ""
        for line_no, line in enumerate(page_text.splitlines(), start=1):
            line = line.replace("\u00ad", "").strip()
            if not line:
                continue
            items.append(
                {
                    "label": "text",
                    "text": line,
                    "prov": [{"page_no": i + 1}],
                    "$ref": None,
                    "_line": line_no,
                }
            )
    return {FORMAT_KEY: PYPDF_FORMAT, "items": items, "n_pages": n_pages}


def convert_pdf(
    pdf_path: PathLike,
    out_json: PathLike | None = None,
    max_pages: int | None = None,
    use_cache: bool = True,
    allow_pypdf_fallback: bool = False,
) -> dict:
    """Конвертирует PDF нормативного документа в структурированный JSON.

    Args:
        pdf_path: путь к PDF (СП, СНиП, ГОСТ...).
        out_json: путь для кэша результата. По умолчанию
            ``<pdf_stem>.docling.json`` рядом с исходником.
        max_pages: ограничить число первых страниц (стабильность/OOM).
        use_cache: перечитывать кэш, если он свежее исходника.
        allow_pypdf_fallback: явно разрешить низкокачественный pypdf-fallback,
            если docling недоступен или его конвертация сорвалась.
            По умолчанию — нет: вместо тихого снижения качества поднимается
            ConversionError.

    Returns:
        dict — сериализованный DoclingDocument (или fallback-структура pypdf,
        если это было явно разрешено).

    Поднимает:
        DocumentLoadError: файл не найден / не читается.
        ConversionError: конвертация завершилась ошибкой.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise DocumentLoadError(f"PDF не найден: {pdf_path}")

    out_json = Path(out_json) if out_json else pdf_path.with_suffix(".docling.json")

    # Кэш: годится, если существует и новее исходника.
    if use_cache and out_json.exists() and out_json.stat().st_mtime >= pdf_path.stat().st_mtime:
        logger.info(f"Кэш конвертации: {out_json.name}")
        with out_json.open(encoding="utf-8") as fh:
            return json.load(fh)

    errors = []
    if is_docling_available():
        try:
            export = _convert_with_docling(pdf_path, max_pages)
            _write_cache(export, out_json)
            return export
        except Exception as exc:  # noqa: BLE001 - фиксируем и решаем про fallback
            errors.append(f"docling: {exc}")
            logger.error(f"Docling конвертация не удалась: {exc}")
    else:
        errors.append("docling: пакет не установлен")

    if not allow_pypdf_fallback:
        if not is_docling_available():
            raise ConversionError(
                "Пакет 'docling' не установлен. Установите его командой:\n"
                "  pip install 'docling>=2.0,<3'\n"
                "(рекомендуется среда с >=4 ГБ RAM; лёгкие CPU-опции уже включены).\n"
                "Либо явно разрешите низкокачественный fallback: allow_pypdf_fallback=True."
            )
        raise ConversionError(
            f"Не удалось сконвертировать {pdf_path.name}: " + " | ".join(errors)
            + "\n(для аварийного pypdf-режима передайте allow_pypdf_fallback=True)"
        )

    logger.warning("Использую pypdf-fallback по явному запросу (качество чанков ниже).")
    try:
        export = _convert_with_pypdf(pdf_path, max_pages)
        _write_cache(export, out_json)
        return export
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf: {exc}")
        raise ConversionError(
            f"Не удалось сконвертировать {pdf_path.name}. " + " | ".join(errors)
        ) from exc


def _write_cache(export: dict, out_json: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as fh:
        json.dump(export, fh, ensure_ascii=False)
    logger.info(f"Сохранён кэш конвертации: {out_json}")
