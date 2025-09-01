"""Батчевая обработка эмбеддингов с улучшенным контролем."""
import logging
import asyncio
from typing import Any
from dataclasses import dataclass

from models.chunk import Chunk
from .embedding_processor import EmbeddingProcessor, EmbeddingStats
from .yandex_client import YandexEmbeddingClient

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """Конфигурация батчевой обработки."""
    batch_size: int = 10
    max_concurrent_batches: int = 3
    delay_between_batches: float = 0.5  # секунды
    progress_callback: Any = None

class BatchEmbeddingProcessor:
    """Продвинутый батчевый процессор с контролем параллелизма."""
    
    def __init__(self, client: YandexEmbeddingClient, config: BatchConfig = None):
        self.client = client
        self.config = config or BatchConfig()
        self.processor = EmbeddingProcessor(client, self.config.batch_size)
    
    async def process_chunks_advanced(self, chunks: list[Chunk]) -> tuple[list[Chunk], EmbeddingStats]:
        """
        Продвинутая обработка с контролем параллелизма и rate limiting.
        
        Args:
            chunks: Список чанков
            
        Returns:
            tuple[list[Chunk], EmbeddingStats]: (обработанные чанки, статистика)
        """
        if not chunks:
            return [], EmbeddingStats(0, 0, 0, 0, 0)
        
        logger.info(
            f"Starting advanced batch processing: {len(chunks)} chunks, "
            f"batch_size={self.config.batch_size}, "
            f"max_concurrent={self.config.max_concurrent_batches}"
        )
        
        # Создаем батчи
        batches = []
        for i in range(0, len(chunks), self.config.batch_size):
            batch = chunks[i:i + self.config.batch_size]
            batches.append((i, batch))
        
        # Семафор для контроля параллелизма
        semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
        
        # Общая статистика
        total_stats = EmbeddingStats(
            total_chunks=len(chunks),
            processed_chunks=0,
            failed_chunks=0,
            total_tokens=0,
            total_characters=0
        )
        
        processed_chunks = []
        
        async def process_batch_with_semaphore(batch_index: int, batch: list[Chunk]) -> None:
            """Обработать батч с семафором."""
            async with semaphore:
                try:
                    logger.debug(f"Processing batch {batch_index + 1}/{len(batches)}")
                    
                    # Обрабатываем батч
                    batch_texts = [chunk.text for chunk in batch]
                    embeddings_results = await self.client.get_embeddings_batch(batch_texts)
                    
                    # Применяем результаты
                    for chunk, (embedding, num_tokens) in zip(batch, embeddings_results):
                        chunk.vector = embedding
                        processed_chunks.append(chunk)
                        
                        # Обновляем статистику (thread-safe не нужен в asyncio)
                        total_stats.processed_chunks += 1
                        total_stats.total_tokens += num_tokens
                        total_stats.total_characters += len(chunk.text)
                    
                    # Progress callback
                    if self.config.progress_callback:
                        self.config.progress_callback(len(processed_chunks), len(chunks))
                    
                    logger.debug(f"Batch {batch_index + 1} completed successfully")
                    
                    # Rate limiting между батчами
                    if self.config.delay_between_batches > 0:
                        await asyncio.sleep(self.config.delay_between_batches)
                        
                except Exception as e:
                    logger.error(f"Batch {batch_index + 1} failed: {e}")
                    
                    # Добавляем чанки без эмбеддингов
                    for chunk in batch:
                        processed_chunks.append(chunk)
                        total_stats.failed_chunks += 1
        
        # Запускаем все батчи параллельно (но с ограничением семафора)
        tasks = [
            process_batch_with_semaphore(batch_index, batch) 
            for batch_index, batch in batches
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(
            f"Advanced batch processing complete: "
            f"{total_stats.processed_chunks} successful, "
            f"{total_stats.failed_chunks} failed"
        )
        
        return processed_chunks, total_stats
