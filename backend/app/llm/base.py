from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLM(ABC):
    """LLM 抽象基类，所有提供商实现在此处继承"""

    @abstractmethod
    async def chat(self, messages: list[dict], stream: bool = False) -> AsyncIterator[str]:
        """流式对话，逐 token yield"""
        ...

    @abstractmethod
    async def chat_complete(self, messages: list[dict]) -> str:
        """非流式对话，返回完整结果"""
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """文本向量化"""
        ...
