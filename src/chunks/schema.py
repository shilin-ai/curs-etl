from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
import uuid as uuid_pkg


class Chunk(BaseModel):
    """
    Chunk schema for multi-source documents.

    This schema is designed to be compact but expressive for Qdrant payloads.
    It separates identity, provenance, and content while avoiding redundancy.
    """

    # Stable identifiers
    source_type: str = Field(..., description="Data source type: confluence|youtrack|gitlab|yandex_disk|miro|n8n|website|video")
    source_id: str = Field(..., description="Identifier in the source system (e.g., page id, issue id)")
    document_id: str = Field(..., description="Logical document id within the source (e.g., page, issue, file)")
    chunk_id: str = Field(..., description="Stable id of this chunk within the document")

    # Content and display
    title: Optional[str] = Field(None, description="Title of the document or chunk")
    url: Optional[HttpUrl] = Field(None, description="Canonical URL to view the source item")
    text: str = Field(..., description="Plaintext content of the chunk (preprocessed)")
    mime: Optional[str] = Field(None, description="MIME type of the source content, e.g., text/html, text/plain, video/mp4")
    language: Optional[str] = Field(None, description="BCP-47 language tag if known, e.g., en, ru")

    # Time metadata (ISO 8601 UTC)
    created_at: Optional[datetime] = Field(None, description="Creation time of the source item or chunk")
    updated_at: Optional[datetime] = Field(None, description="Last update time of the source item or chunk")

    # Additional metadata
    tags: Optional[List[str]] = Field(default=None, description="Arbitrary tags for filtering and ranking")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Source-specific extra fields (lightweight only)")

    @validator("source_type")
    def validate_source_type(cls, v: str) -> str:
        return v.strip().lower()

    @validator("tags")
    def normalize_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        normalized = []
        for tag in v:
            t = (tag or "").strip().lower()
            if t:
                normalized.append(t)
        return normalized or None


def build_point_id(document_id: str, chunk_id: str) -> str:
    """
    Build deterministic UUIDv5 for the point id from document and chunk ids.
    Ensures stable ids across re-ingestion runs.
    """
    namespace = uuid_pkg.UUID("00000000-0000-0000-0000-000000000000")
    return str(uuid_pkg.uuid5(namespace, f"{document_id}:{chunk_id}"))


def chunk_to_payload(chunk: Chunk) -> Dict[str, Any]:
    """
    Convert Chunk to a compact Qdrant payload dict.
    Avoids nesting where not needed, to keep filter operations fast.
    """
    payload: Dict[str, Any] = {
        "source_type": chunk.source_type,
        "source_id": chunk.source_id,
        "document_id": chunk.document_id,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "url": str(chunk.url) if chunk.url else None,
        "text": chunk.text,
        "mime": chunk.mime,
        "language": chunk.language,
        "created_at": chunk.created_at.isoformat().replace("+00:00", "Z") if chunk.created_at else None,
        "updated_at": chunk.updated_at.isoformat().replace("+00:00", "Z") if chunk.updated_at else None,
        "tags": chunk.tags,
    }
    # Merge extra but avoid collisions
    if chunk.extra:
        for key, value in chunk.extra.items():
            if key in payload:
                continue
            payload[key] = value
    # Remove Nones for compactness
    return {k: v for k, v in payload.items() if v is not None}

