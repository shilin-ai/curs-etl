"""Создание чанков с метаданными."""
import logging
from dataclasses import dataclass

from models.chunk import Chunk
from .text_splitter import TextSplitter

logger = logging.getLogger(__name__)

@dataclass 
class ChunkPayload:
    """Payload данные для создания чанка.
    
    Все поля кроме id и vector попадают в Qdrant payload.
    Поле metadata содержит специфичные для источника данные.
    """
    source: str
    chunk_type: str  
    id_in_source: str
    title: str | None = None
    url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    author: str | None = None
    # metadata - опциональные данные специфичные для источника
    metadata: dict[str, any] | None = None

class ChunkBuilder:
    def __init__(self, text_splitter: TextSplitter):
        self.text_splitter = text_splitter
    
    def build_chunks(self, text: str, payload: ChunkPayload) -> list[Chunk]:
        """Создать чанки из текста с payload данными."""
        if not text or not text.strip():
            return []
            
        raw_chunks = self.text_splitter.split(text)
        if not raw_chunks:
            return []
            
        chunks: list[Chunk] = []
        total_chunks = len(raw_chunks)
        
        for idx, chunk_text in enumerate(raw_chunks):
            norm_text = chunk_text.strip()
            if not norm_text:
                continue

            chunk = Chunk(
                source=payload.source,
                type=payload.chunk_type,
                id_in_source=payload.id_in_source,
                title=payload.title,
                url=payload.url,
                text=norm_text,
                chunk_index=idx,
                chunk_count=total_chunks,
                created_at=payload.created_at,
                updated_at=payload.updated_at,
                author=payload.author,
                # metadata - только специфичные для источника данные
                metadata=payload.metadata or {},
            )
            chunks.append(chunk)

        logger.debug(f"Built {len(chunks)} chunks")
        return chunks

    def build_single_chunk(self, text: str, payload: ChunkPayload) -> Chunk:
        """Создать один чанк без разбиения (для коротких текстов)."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        return Chunk(
            source=payload.source,
            type=payload.chunk_type,
            id_in_source=payload.id_in_source,
            title=payload.title,
            url=payload.url,
            text=text.strip(),
            chunk_index=0,
            chunk_count=1,
            created_at=payload.created_at,
            updated_at=payload.updated_at,
            author=payload.author,
            # metadata - только специфичные для источника данные
            metadata=payload.metadata or {},
        )
