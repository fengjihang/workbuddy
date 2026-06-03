from .store import get_or_create_collection
from .embedder import Embedder


class Retriever:
    """知识库检索"""

    def __init__(self, embedder: Embedder):
        self._embedder = embedder

    async def retrieve(self, collection_name: str, query: str, top_k: int = 5) -> list[str]:
        collection = get_or_create_collection(collection_name)
        embeddings = await self._embedder.embed([query])
        results = collection.query(query_embeddings=embeddings, n_results=top_k)
        documents = results.get("documents", [[]])[0]
        return documents

    def add_documents(self, collection_name: str, ids: list[str], documents: list[str], metadatas: list[dict] | None = None):
        collection = get_or_create_collection(collection_name)
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def delete_documents(self, collection_name: str, ids: list[str]):
        collection = get_or_create_collection(collection_name)
        collection.delete(ids=ids)
