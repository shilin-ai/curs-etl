# utils/common/id_generator.py
"""Генерация детерминистских ID для чанков."""
import hashlib
from uuid import uuid5, NAMESPACE_URL

class ChunkIDGenerator:
    """Генерирует детерминистские ID согласно QDRANT_CHUNK.md"""
    
    @staticmethod
    def generate_deterministic_id(source: str, id_in_source: str, chunk_index: int) -> str:
        """
        Генерирует детерминистский UUID v5 для чанка.
        
        Формат: uuid5(namespace, f"{source}|{id_in_source}|{chunk_index}")
        """
        namespace_string = f"{source}|{id_in_source}|{chunk_index}"
        return str(uuid5(NAMESPACE_URL, namespace_string))
    
    @staticmethod
    def generate_content_hash(text: str) -> str:
        """Генерирует хеш содержимого для детекции изменений."""
        return hashlib.md5(text.encode()).hexdigest()[:8]