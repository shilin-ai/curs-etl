from __future__ import annotations

from typing import Dict, Any, Optional, Sequence
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    TextIndexParams,
    TokenizerType,
    PayloadSchemaType,
)

from .schema import Chunk, chunk_to_payload, build_point_id


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    *,
    vector_size: int,
    distance: Distance = Distance.COSINE,
    on_disk: bool = False,
) -> None:
    """
    Ensure Qdrant collection exists with vector params and basic payload indexes.

    - Creates collection if missing
    - Sets up full-text index for title and text
    - Sets up keyword indexes for source_type, document_id, chunk_id, tags
    """
    existing = None
    try:
        existing = client.get_collection(collection_name)
    except Exception:
        existing = None

    if not existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance, on_disk=on_disk),
        )

    # Create payload indexes (idempotent; Qdrant ignores duplicates)
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="title",
            field_schema=PayloadSchemaType.TEXT,
            text_index_params=TextIndexParams(tokenizer=TokenizerType.WORD, lowercase=True, min_token_len=2),
        )
    except Exception:
        pass

    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="text",
            field_schema=PayloadSchemaType.TEXT,
            text_index_params=TextIndexParams(tokenizer=TokenizerType.WORD, lowercase=True, min_token_len=2),
        )
    except Exception:
        pass

    for keyword_field in ("source_type", "document_id", "chunk_id", "language", "mime"):
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=keyword_field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass

    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="tags",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        pass


def upsert_chunk(
    client: QdrantClient,
    collection_name: str,
    *,
    chunk: Chunk,
    vector: Sequence[float],
    wait: bool = True,
    point_id: Optional[str] = None,
    payload_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Upsert a single chunk into Qdrant and return the point id.

    - Uses deterministic id by default based on document_id + chunk_id
    - Allows payload overrides for caller-specific additions
    """
    pid = point_id or build_point_id(chunk.document_id, chunk.chunk_id)
    payload = chunk_to_payload(chunk)
    if payload_overrides:
        payload.update(payload_overrides)

    point = PointStruct(id=pid, vector=vector, payload=payload)
    client.upsert(collection_name=collection_name, wait=wait, points=[point])
    return pid

