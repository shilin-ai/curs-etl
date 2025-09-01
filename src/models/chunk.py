from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid
from datetime import datetime


@dataclass
class Chunk:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vector: list[float] = field(default_factory=list)

    source: str = ""        # gitlab | confluence | youtrack | yandex_disk | miro | n8n | website | ...
    type: str = ""          # file | commit | page | ticket | doc | board | workflow | site_page | video | ...

    id_in_source: str = ""  # стабильный идентификатор внутри источника
    title: str | None = None
    url: str | None = None
    text: str = ""

    chunk_index: int = 0
    chunk_count: int = 1

    created_at: str | None = None  # ISO8601
    updated_at: str | None = None
    author: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_qdrant_point(self) -> dict[str, Any]:
        """Преобразовать чанк в формат Qdrant PointStruct"""
        return {
            "id": self.id,
            "vector": self.vector,
            "payload": {
                "source": self.source,
                "type": self.type,
                "id_in_source": self.id_in_source,
                "title": self.title,
                "url": self.url,
                "text": self.text,
                "chunk_index": self.chunk_index,
                "chunk_count": self.chunk_count,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "author": self.author,
                "metadata": self.metadata,
            },
        }
