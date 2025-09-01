"""Клиент для работы с Yandex Foundation Models Embedding API."""
import logging
import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class YandexEmbeddingConfig:
    """Конфигурация для Yandex Foundation Models."""
    folder_id: str
    auth: str | None = None
    iam_token: str | None = None
    embed_model: str = "text-search-query/latest"
    embedding_dimension: int | None = None
    request_timeout: int = 60
    max_retries: int = 3
    api_endpoint: str = "https://llm.api.cloud.yandex.net"

class YandexEmbeddingError(Exception):
    """Ошибка при работе с Yandex Embedding API."""
    pass

class YandexEmbeddingClient:
    """Клиент для получения эмбеддингов через Yandex Foundation Models API."""
    
    def __init__(self, config: YandexEmbeddingConfig):
        self.config = config
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Проверить корректность конфигурации."""
        if not self.config.folder_id:
            raise YandexEmbeddingError("folder_id is required")
        
        if not self.config.api_key and not self.config.iam_token:
            raise YandexEmbeddingError("Either api_key or iam_token must be provided")
            
        if self.config.api_key and self.config.iam_token:
            logger.warning("Both api_key and iam_token provided, using api_key")
    
    def _get_model_uri(self) -> str:
        """Получить URI модели."""
        return f"emb://{self.config.folder_id}/{self.config.embed_model}"
    
    def _get_headers(self) -> dict[str, str]:
        """Получить заголовки для запроса."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.config.api_key:
            headers["Authorization"] = f"Api-Key {self.config.api_key}"
        elif self.config.iam_token:
            headers["Authorization"] = f"Bearer {self.config.iam_token}"
            
        return headers
    
    async def get_embedding(self, text: str) -> tuple[list[float], int]:
        """
        Получить эмбеддинг для одного текста.
        
        Returns:
            tuple[list[float], int]: (embedding, num_tokens)
        """
        if not text or not text.strip():
            raise YandexEmbeddingError("Text cannot be empty")
        
        # Подготовка запроса
        request_body = {
            "modelUri": self._get_model_uri(),
            "text": text.strip()
        }
        
        # Добавить dimension если указан
        if self.config.embedding_dimension:
            request_body["dim"] = str(self.config.embedding_dimension)
        
        url = f"{self.config.api_endpoint}/foundationModels/v1/textEmbedding"
        headers = self._get_headers()
        
        # Выполнение запроса с retry логикой
        for attempt in range(self.config.max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as session:
                    async with session.post(url, json=request_body, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            embedding = [float(x) for x in result["embedding"]]
                            num_tokens = int(result.get("numTokens", 0))
                            
                            logger.debug(f"Got embedding for text ({len(text)} chars, {num_tokens} tokens)")
                            return embedding, num_tokens
                        else:
                            error_text = await response.text()
                            raise YandexEmbeddingError(f"API error {response.status}: {error_text}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.config.max_retries}")
                if attempt == self.config.max_retries - 1:
                    raise YandexEmbeddingError("Request timeout after all retries")
            except aiohttp.ClientError as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{self.config.max_retries}: {e}")
                if attempt == self.config.max_retries - 1:
                    raise YandexEmbeddingError(f"Network error after all retries: {e}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.config.max_retries - 1:
                    raise YandexEmbeddingError(f"Unexpected error: {e}")
            
            # Exponential backoff
            if attempt < self.config.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        raise YandexEmbeddingError("Failed after all retries")

    async def get_embeddings_batch(self, texts: list[str]) -> list[tuple[list[float], int]]:
        """
        Получить эмбеддинги для списка текстов параллельно.
        
        Returns:
            list[tuple[list[float], int]]: List of (embedding, num_tokens) for each text
        """
        if not texts:
            return []
        
        logger.info(f"Processing {len(texts)} texts for embeddings")
        
        # Фильтруем пустые тексты
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        
        if not valid_texts:
            logger.warning("No valid texts to process")
            return []
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for i, text in valid_texts:
            task = self.get_embedding(text)
            tasks.append((i, task))
        
        # Выполняем все задачи
        results = [None] * len(texts)  # Placeholder для результатов
        
        try:
            # Выполняем все задачи параллельно
            completed_tasks = await asyncio.gather(
                *[task for _, task in tasks], 
                return_exceptions=True
            )
            
            # Обрабатываем результаты
            successful_embeddings = 0
            failed_embeddings = 0
            
            for (original_index, _), result in zip(tasks, completed_tasks):
                if isinstance(result, Exception):
                    logger.error(f"Failed to get embedding for text {original_index}: {result}")
                    results[original_index] = None
                    failed_embeddings += 1
                else:
                    results[original_index] = result
                    successful_embeddings += 1
            
            logger.info(f"Embeddings completed: {successful_embeddings} successful, {failed_embeddings} failed")
            
            # Возвращаем только успешные результаты, фильтруя None
            return [result for result in results if result is not None]
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise YandexEmbeddingError(f"Batch processing error: {e}")
