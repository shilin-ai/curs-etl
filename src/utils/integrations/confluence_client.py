"""Клиент для работы с Confluence API."""
import logging
from dataclasses import dataclass
from atlassian import Confluence

logger = logging.getLogger(__name__)

@dataclass
class ConfluenceConfig:
    """Конфигурация подключения к Confluence."""
    url: str
    token: str
    space_keys: list[str]

@dataclass
class PaginationConfig:
    """Настройки пагинации."""
    limit: int = 100
    max_retries: int = 3

class ConfluenceAPIError(Exception):
    """Ошибка при работе с Confluence API."""
    pass

class ConfluenceClient:
    """Клиент для извлечения данных из Confluence."""
    
    def __init__(self, config: ConfluenceConfig, pagination: PaginationConfig = None):
        self.config = config
        self.pagination = pagination or PaginationConfig()
        
        try:
            self._client = Confluence(
                url=config.url,
                token=config.token
            )
            logger.info(f"Connected to Confluence: {config.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Confluence: {e}")
            raise ConfluenceAPIError(f"Connection failed: {e}") from e
    
    def get_space_pages(self, space_key: str) -> list[dict]:
        """Получить все страницы из одного пространства."""
        if not space_key or not space_key.strip():
            logger.warning(f"Skipping empty space key: '{space_key}'")
            return []
            
        logger.info(f"Starting extraction from space: {space_key}")
        
        all_pages = []
        start = 0
        
        try:
            while True:
                logger.debug(f"Fetching pages from space '{space_key}', start: {start}")
                
                pages = self._fetch_pages_batch(space_key, start)
                if not pages:
                    break
                    
                all_pages.extend(pages)
                logger.info(f"Retrieved {len(pages)} pages from space '{space_key}', start: {start}")
                
                if len(pages) < self.pagination.limit:
                    break
                    
                start += self.pagination.limit
                
            logger.info(f"Completed extraction from space '{space_key}': {len(all_pages)} pages")
            return all_pages
            
        except Exception as e:
            logger.error(f"Error extracting pages from space '{space_key}': {e}")
            raise ConfluenceAPIError(f"Failed to extract from space {space_key}: {e}") from e
    
    def get_all_pages(self) -> list[dict]:
        """Получить все страницы из всех настроенных пространств."""
        logger.info(f"Starting extraction from {len(self.config.space_keys)} spaces")
        
        all_pages = []
        failed_spaces = []
        
        for space_key in self.config.space_keys:
            try:
                logger.info(f"Processing space: {space_key}")
                pages = self.get_space_pages(space_key)
                all_pages.extend(pages)
                
            except ConfluenceAPIError as e:
                logger.error(f"Failed to process space '{space_key}': {e}")
                failed_spaces.append(space_key)
                continue  # Продолжаем с другими пространствами
        
        if failed_spaces:
            logger.warning(f"Failed to process {len(failed_spaces)} spaces: {failed_spaces}")
        
        logger.info(f"Total pages extracted: {len(all_pages)} from {len(self.config.space_keys) - len(failed_spaces)} spaces")
        return all_pages
    
    def _fetch_pages_batch(self, space_key: str, start: int) -> list[dict]:
        """Получить batch страниц с retry логикой."""
        for attempt in range(self.pagination.max_retries):
            try:
                pages = self._client.get_all_pages_from_space(
                    space_key,
                    start=start,
                    limit=self.pagination.limit,
                    status=None,
                    expand="body.storage,version,space",
                    content_type='page'
                )
                return pages
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.pagination.max_retries} failed for space '{space_key}', start {start}: {e}")
                if attempt == self.pagination.max_retries - 1:
                    raise
                    
        return []
