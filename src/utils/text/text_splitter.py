"""Разбиение текста на чанки."""
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class TextSplittingError(Exception):
    pass

class TextSplitter:
    def __init__(self, chunk_size: int, overlap: int):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
        )
    
    def split(self, text: str) -> list[str]:
        """Разбить текст на чанки."""
        if not text or not text.strip():
            return []
            
        try:
            chunks = self._splitter.split_text(text)
            logger.debug(f"Split text: {len(chunks)} chunks")
            return [chunk for chunk in chunks if chunk.strip()]
            
        except Exception as e:
            logger.error(f"Text splitting failed: {e}")
            raise TextSplittingError(f"Failed to split text: {e}") from e
