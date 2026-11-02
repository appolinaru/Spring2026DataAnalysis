"""arch_rag — библиотека поиска по архитектурным нормативам."""

from arch_rag.core.norms import NormsSearcher
from arch_rag.core.vector_search import VectorSearcher
from arch_rag.exceptions import (
    ArchRAGError,
    ConversionError,
    DocumentLoadError,
    EmptyQueryError,
    NoResultsError,
)
from arch_rag.ingestion.chunker import chunk_document, load_norms_json, save_norms_json
from arch_rag.ingestion.docling_converter import convert_pdf, is_docling_available
from arch_rag.services.concept_builder import ConceptBuilder

__all__ = [
    "NormsSearcher",
    "VectorSearcher",
    "ConceptBuilder",
    "ArchRAGError",
    "EmptyQueryError",
    "NoResultsError",
    "ConversionError",
    "DocumentLoadError",
    "convert_pdf",
    "is_docling_available",
    "chunk_document",
    "save_norms_json",
    "load_norms_json",
]
