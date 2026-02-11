from abc import ABC, abstractmethod
from typing import List, Dict
from core.models import KnowledgeBase, QueryRequest, QueryResponse

class KnowledgeBaseProvider(ABC):
    @abstractmethod
    async def list_knowledge_bases(self) -> Dict[str, KnowledgeBase]:
        """List all available knowledge bases."""
        pass

    @abstractmethod
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query a knowledge base."""
        pass
