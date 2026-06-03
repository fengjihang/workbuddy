from ..llm.openai_compat import OpenAICompatibleLLM


class Embedder:
    """文本向量化封装"""

    def __init__(self, llm: OpenAICompatibleLLM):
        self._llm = llm

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._llm.embed(texts)
