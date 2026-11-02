"""Ингестация нормативного PDF: Docling → чанки норм → JSON для поиска.

Использование:

    python examples/ingest.py data/sp54.pdf --out data/norms.json
    python examples/ingest.py data/sp54.pdf --max-pages 20 --no-cache

После этого нормы подключаются к поиску без изменения ядра:

    from arch_rag import NormsSearcher, VectorSearcher, load_norms_json

    norms = load_norms_json("data/norms.json")
    searcher = NormsSearcher(norms)
    vsearcher = VectorSearcher(norms)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from arch_rag.exceptions import ArchRAGError
from arch_rag.ingestion import chunk_document, convert_pdf, save_norms_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Конвертация PDF норматива (СП/СНиП/ГОСТ) в нормы для RAG-поиска."
    )
    parser.add_argument("pdf", help="Путь к PDF-документу")
    parser.add_argument(
        "--out",
        default=None,
        help="Куда сохранить нормы (JSON). По умолчанию <pdf_stem>.norms.json",
    )
    parser.add_argument(
        "--cache",
        default=None,
        help="Путь кэша конвертации (по умолчанию <pdf_stem>.docling.json)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=None, help="Обрабатывать только первые N страниц"
    )
    parser.add_argument("--no-cache", action="store_true", help="Игнорировать существующий кэш")
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help=(
            "Разрешить pypdf-fallback, если docling недоступен/сорвался. "
            "Внимание: качество чанков заметно ниже, чем у Docling."
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Отладочный лог")
    args = parser.parse_args()

    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.verbose else "INFO")

    try:
        export = convert_pdf(
            args.pdf,
            out_json=args.cache,
            max_pages=args.max_pages,
            use_cache=not args.no_cache,
            allow_pypdf_fallback=args.allow_fallback,
        )
        norms = chunk_document(export)
        out_path = Path(args.out) if args.out else Path(args.pdf).with_suffix(".norms.json")
        save_norms_json(norms, out_path)
    except ArchRAGError as exc:
        print(f"Ошибка ингестации: {exc}", file=sys.stderr)
        return 1

    # Короткая сводка
    sections = sorted({n["section"] for n in norms if n.get("section")})
    print(f"\nГотово: {len(norms)} норм сохранено в {out_path}")
    print(f"Разделы: {', '.join(sections[:15])}{' ...' if len(sections) > 15 else ''}")
    for n in norms[:3]:
        print(f"  [{n['type']} {n['number']}, п. {n['section']}] {n['text'][:80]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
