from abc import ABC, abstractmethod
from typing import List, Dict
from src.core.models import KnowledgeBase, QueryRequest, QueryResponse

class KnowledgeBaseProvider(ABC):
    @abstractmethod
    async def list_knowledge_bases(self) -> Dict[str, KnowledgeBase]:
        """List all available knowledge bases."""
        pass

    @abstractmethod
    async def retrieve(self, request: QueryRequest) -> QueryResponse:
        """Retrieve chunks from a knowledge base."""
        pass

    @abstractmethod
    async def retrieve_and_generate(self, request: QueryRequest) -> QueryResponse:
        """Retrieve chunks from a knowledge base and generate an answer."""
        pass
