import os
from dotenv import load_dotenv
from types import SimpleNamespace

# Загружаем переменные окружения из .env файла
load_dotenv()

# Рекурсивно преобразует словарь в SimpleNamespace для удобного доступа к настройкам
def ns(d: dict) -> SimpleNamespace:
    """Преобразует dict в SimpleNamespace рекурсивно"""
    return SimpleNamespace(**{
        k: ns(v) if isinstance(v, dict) else v
        for k, v in d.items()
    })

# Основной словарь с настройками проекта, собирается из переменных окружения
_settings = {
    "confluence": {
        "url": os.getenv("CONFLUENCE_URL"),
        "token": os.getenv("CONFLUENCE_TOKEN"),
        "space_keys": os.getenv("CONFLUENCE_SPACE_KEYS", "").split(","),
        "updated_after": os.getenv("CONFLUENCE_UPDATED_AFTER"),
        "page_limit": int(os.getenv("CONFLUENCE_PAGE_LIMIT", "100")),
    },
    "qdrant": {
        "url": os.getenv("QDRANT_URL"),
        "api_key": os.getenv("QDRANT_API_KEY"),
        "collection": os.getenv("QDRANT_COLLECTION", "confluence_docs"),
        "vector_size": int(os.getenv("VECTOR_SIZE", "1536")),
    },
    "yandex": {
        "folder_id": os.getenv("YANDEX_FOLDER_ID"),
        "auth": os.getenv("YANDEX_AUTH"),
        "embed_model": os.getenv("YANDEX_EMBED_MODEL", "foundation-models/embedding-ge-text-v1"),
        "gpt_model": os.getenv("YANDEX_GPT_MODEL", "foundation-models/gpt-ge-text"),
        "batch_size": int(os.getenv("YANDEX_BATCH_SIZE", "16")),
        "top_k": int(os.getenv("YANDEX_TOP_K", "4")),
        "search_threshold": float(os.getenv("YANDEX_SEARCH_THRESHOLD", "0.55")),
        "embed_dim": int(os.getenv("YANDEX_EMBED_DIM", "256")),
        "request_timeout": int(os.getenv("YANDEX_REQUEST_TIMEOUT", "60")),
        "max_retries": int(os.getenv("YANDEX_MAX_RETRIES", "3")),
    },
    "chunking": {
        "size": int(os.getenv("CHUNK_SIZE", "512")),
        "overlap": int(os.getenv("CHUNK_OVERLAP", "64")),
    },
    "mattermost": {
        "url": os.getenv("MATTERMOST_URL"),
        "scheme": os.getenv("MATTERMOST_SCHEME"),
        "token": os.getenv("MATTERMOST_TOKEN"),
        "bot_user_id": os.getenv("MATTERMOST_BOT_USER_ID"),
        "bot_name": os.getenv("MATTERMOST_BOT_NAME"),
    },
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"),
    },
    "gitlab": {
        "url": os.getenv("GITLAB_URL"),
        "token": os.getenv("GITLAB_TOKEN"),
        "group_id": int(os.getenv("GITLAB_GROUP_ID", "0")),
        "file_exts": os.getenv("GITLAB_FILE_EXTS", ".py,.md").split(","),
    },
}

# Глобальный объект настроек для всего проекта
settings = ns(_settings)
