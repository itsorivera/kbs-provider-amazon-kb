from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DataSource(BaseModel):
    id: str
    name: str

class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    data_sources: List[DataSource] = Field(default_factory=list)

class QueryRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[str] = None
    data_source_ids: Optional[List[str]] = None
    num_results: int = 20
    reranking: bool = False

class SearchResult(BaseModel):
    content: Dict[str, Any]
    location: Dict[str, Any]
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[SearchResult]
    answer: Optional[str] = None
