import json
from atlassian import Confluence
from config.settings import settings
from config.logger import get_logger, setup_logger
from utils.integrations.confluence_client import ConfluenceConfig, PaginationConfig, ConfluenceClient
from utils.integrations.confluence_processor import ConfluenceProcessor
from utils.text.text_splitter import TextSplitter
from utils.text.chunk_builder import ChunkBuilder


logger = setup_logger("etl_pipeline", level="INFO")

config = ConfluenceConfig(
            url=settings.confluence.url,
            token=settings.confluence.token,
            space_keys=settings.confluence.space_keys
)
pagination = PaginationConfig(limit=200, max_retries=3)
client = ConfluenceClient(config,pagination)
text_splitter = TextSplitter(settings.chunking.size, settings.chunking.overlap)
chunk_builder = ChunkBuilder(text_splitter)
processor = ConfluenceProcessor(client, chunk_builder)

    # Обработка
chunks, texts = processor.extract_and_process()
print(chunks)