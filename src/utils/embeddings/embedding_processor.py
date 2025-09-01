"""Обработчик эмбеддингов для чанков."""
import logging
import asyncio
from dataclasses import dataclass

from models.chunk import Chunk
from utils.common.progress_tracker import ProgressTracker
from .yandex_client import YandexEmbeddingClient, YandexEmbeddingConfig

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingStats:
    """Статистика обработки эмбеддингов."""
    total_chunks: int
    processed_chunks: int
    failed_chunks: int
    total_tokens: int
    total_characters: int

class EmbeddingProcessor:
    """Процессор для добавления эмбеддингов к чанкам."""
    
    def __init__(self, client: YandexEmbeddingClient, batch_size: int = 10):
        self.client = client
        self.batch_size = batch_size
    
    async def process_chunks(self, chunks: list[Chunk]) -> tuple[list[Chunk], EmbeddingStats]:
        """
        Обработать чанки и добавить к ним эмбеддинги.
        
        Args:
            chunks: Список чанков для обработки
            
        Returns:
            tuple[list[Chunk], EmbeddingStats]: (обновленные чанки, статистика)
        """
        if not chunks:
            logger.warning("No chunks to process for embeddings")
            return [], EmbeddingStats(0, 0, 0, 0, 0)
        
        logger.info(f"Processing embeddings for {len(chunks)} chunks in batches of {self.batch_size}")
        
        # Статистика
        stats = EmbeddingStats(
            total_chunks=len(chunks),
            processed_chunks=0,
            failed_chunks=0,
            total_tokens=0,
            total_characters=0
        )
        
        progress = ProgressTracker(len(chunks), "chunks")
        updated_chunks = []
        
        # Обрабатываем батчами
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_texts = [chunk.text for chunk in batch]
            
            try:
                # Получаем эмбеддинги для батча
                embeddings_results = await self.client.get_embeddings_batch(batch_texts)
                
                # Применяем эмбеддинги к чанкам
                for j, (chunk, (embedding, num_tokens)) in enumerate(zip(batch, embeddings_results)):
                    chunk.vector = embedding
                    updated_chunks.append(chunk)
                    
                    # Обновляем статистику
                    stats.processed_chunks += 1
                    stats.total_tokens += num_tokens
                    stats.total_characters += len(chunk.text)
                    
                    progress.update(i + j + 1)
                
            except Exception as e:
                logger.error(f"Failed to process batch {i//self.batch_size + 1}: {e}")
                
                # Добавляем чанки без эмбеддингов
                for chunk in batch:
                    updated_chunks.append(chunk)  # vector остается пустым
                    stats.failed_chunks += 1
                    
                progress.update(i + len(batch))
        
        logger.info(
            f"Embedding processing complete: "
            f"{stats.processed_chunks} successful, {stats.failed_chunks} failed, "
            f"{stats.total_tokens} tokens, {stats.total_characters} characters"
        )
        
        return updated_chunks, stats
    
    async def process_single_chunk(self, chunk: Chunk) -> Chunk:
        """
        Обработать один чанк и добавить эмбеддинг.
        
        Args:
            chunk: Чанк для обработки
            
        Returns:
            Chunk: Обновленный чанк с эмбеддингом
        """
        try:
            embedding, num_tokens = await self.client.get_embedding(chunk.text)
            chunk.vector = embedding
            logger.debug(f"Added embedding to chunk {chunk.id} ({num_tokens} tokens)")
            return chunk
        except Exception as e:
            logger.error(f"Failed to add embedding to chunk {chunk.id}: {e}")
            return chunk  # Возвращаем без эмбеддинга
