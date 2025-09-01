"""Очистка HTML контента."""
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HTMLCleaningError(Exception):
    pass

def clean_html(html_content: str) -> str:
    """Удаляет HTML теги и возвращает чистый текст."""
    if not html_content or not html_content.strip():
        return ""
        
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        clean_text = soup.get_text(separator=" ", strip=True)
        
        logger.debug(f"Cleaned HTML: {len(html_content)} -> {len(clean_text)} chars")
        return clean_text
        
    except Exception as e:
        logger.error(f"HTML cleaning failed: {e}")
        raise HTMLCleaningError(f"Failed to clean HTML: {e}") from e
