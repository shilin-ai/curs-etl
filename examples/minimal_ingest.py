from datetime import datetime, timezone
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance

from src.chunks.schema import Chunk
from src.chunks.qdrant_io import ensure_collection, upsert_chunk


def main() -> None:
    client = QdrantClient(url="http://localhost:6333")
    collection = "documents"
    vector_size = 384  # adjust to your embeddings

    ensure_collection(client, collection, vector_size=vector_size, distance=Distance.COSINE)

    chunk = Chunk(
        source_type="confluence",
        source_id="PAGE-123",
        document_id="confluence:space:page-123",
        chunk_id="p1",
        title="Пример страницы",
        url="https://example.com/confluence/page-123",
        text="Это тестовый текст чанка для проверки записи в Qdrant.",
        mime="text/html",
        language="ru",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tags=["doc", "example"],
    )

    # Dummy vector; replace with actual embedding of chunk.text
    vector = [0.0] * vector_size

    point_id = upsert_chunk(client, collection, chunk=chunk, vector=vector)
    print(f"Upserted point id: {point_id}")


if __name__ == "__main__":
    main()

