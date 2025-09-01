"""Обработка данных Confluence с улучшенной архитектурой."""
import logging
from dataclasses import dataclass

from models.chunk import Chunk
from utils.text.html_cleaner import clean_html
from utils.text.chunk_builder import ChunkBuilder, ChunkPayload
from utils.common.progress_tracker import ProgressTracker
from .confluence_client import ConfluenceClient
from utils.embeddings.yandex_client import YandexEmbeddingClient, YandexEmbeddingConfig
from utils.embeddings.embedding_processor import EmbeddingProcessor
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ConfluencePageData:
    id: str
    title: str
    url: str
    content: str
    author: str
    space_key: str
    updated_at: str
    version: int | None = None

class ConfluenceProcessor:
    """Полный pipeline обработки Confluence данных."""
    
    def __init__(self, client: ConfluenceClient, chunk_builder: ChunkBuilder, with_embeddings: bool = True):
        self.client = client
        self.chunk_builder = chunk_builder
        self.with_embeddings = with_embeddings
        
        # Инициализация клиента эмбеддингов
        if self.with_embeddings:
            embedding_config = YandexEmbeddingConfig(
                folder_id=settings.yandex.folder_id,
                api_key=settings.yandex.api_key,
                iam_token=settings.yandex.iam_token,
                embed_model=settings.yandex.embed_model,
                embedding_dimension=settings.yandex.embedding_dimension if settings.yandex.embedding_dimension else None,
                request_timeout=settings.yandex.request_timeout,
                max_retries=settings.yandex.max_retries,
                api_endpoint=settings.yandex.api_endpoint
            )
            embedding_client = YandexEmbeddingClient(embedding_config)
            self.embedding_processor = EmbeddingProcessor(embedding_client, settings.yandex.batch_size)

        self.client = client
        self.chunk_builder = chunk_builder
    
    def extract_and_process(self) -> tuple[list[Chunk], list[str]]:
        """Извлечь данные из Confluence и обработать их в чанки."""
        logger.info("Starting Confluence extraction and processing")
        
        # Извлекаем данные
        pages = self.client.get_all_pages()
        if not pages:
            logger.warning("No pages extracted from Confluence")
            return [], []
        
        # Обрабатываем в чанки
        chunks, texts = self.process_pages(pages)
        
        logger.info(f"Confluence processing complete: {len(chunks)} chunks from {len(pages)} pages")
        return chunks, texts
    
    def process_pages(self, pages: list[dict]) -> tuple[list[Chunk], list[str]]:
        """Обработать страницы в чанки."""
        logger.info(f"Processing {len(pages)} Confluence pages")
        
        all_chunks: list[Chunk] = []
        all_texts: list[str] = []
        skipped_pages = 0
        
        progress = ProgressTracker(len(pages), "pages")
        
        for i, page in enumerate(pages, start=1):
            progress.update(i)
            
            try:
                page_data = self._extract_page_data(page)
                chunks = self._process_single_page(page_data)
                
                if chunks:
                    all_chunks.extend(chunks)
                    all_texts.extend([chunk.text for chunk in chunks])
                else:
                    skipped_pages += 1
                    
            except Exception as e:
                logger.error(f"Error processing page {i}: {e}")
                skipped_pages += 1
                continue
        
        logger.info(f"Processed {len(all_chunks)} chunks, skipped {skipped_pages} pages")
        return all_chunks, all_texts
    
    def _extract_page_data(self, page: dict) -> ConfluencePageData:
        """Извлечь структурированные данные из raw страницы."""
        page_id = str(page.get("id", ""))
        title = page.get("title", "")
        
        # Формируем URL
        base_url = self.client.config.url.rstrip('/')
        url = ""
        if "_links" in page and "webui" in page["_links"]:
            url = f"{base_url}{page['_links']['webui']}"
        
        space_key = page.get("space", {}).get("key", "")
        updated_at = page.get("version", {}).get("when", "")
        version = page.get("version", {}).get("number")
        raw_html = page.get("body", {}).get("storage", {}).get("value", "")
        author = page.get("version", {}).get("by",{}).get("displayName","")

        return ConfluencePageData(
            id=page_id,
            title=title,
            url=url,
            content=raw_html,
            space_key=space_key,
            updated_at=updated_at,
            author=author,
            version=version
        )
    
    def _process_single_page(self, page_data: ConfluencePageData) -> list[Chunk]:
        """Обработать одну страницу в чанки."""
        if not page_data.content:
            logger.debug(f"Skipping page '{page_data.title}' - no content")
            return []
        
        # Очищаем HTML
        text = clean_html(page_data.content)
        if not text or len(text.strip()) < 10:  # Минимальная длина текста
            logger.debug(f"Skipping page '{page_data.title}' - insufficient text after cleaning")
            return []
        
        # Создаем payload
        payload = ChunkPayload(
            source="confluence",
            chunk_type="page",
            id_in_source=page_data.id,
            title=page_data.title,
            url=page_data.url,
            created_at=page_data.updated_at,
            updated_at=page_data.updated_at,
            author=page_data.author,
            metadata={
                "space_key": page_data.space_key,
                "version": page_data.version,
                "content_type": "storage",
                "original_length": len(page_data.content),
                "cleaned_length": len(text)
            }
        )
        
        # Создаем чанки
        return self.chunk_builder.build_chunks(text, payload)
