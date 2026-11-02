"""Загрузка и конвертация нормативных документов (PDF → чанки норм)."""

from arch_rag.ingestion.chunker import chunk_document, load_norms_json, save_norms_json
from arch_rag.ingestion.docling_converter import convert_pdf, is_docling_available

__all__ = [
    "convert_pdf",
    "is_docling_available",
    "chunk_document",
    "save_norms_json",
    "load_norms_json",
]
