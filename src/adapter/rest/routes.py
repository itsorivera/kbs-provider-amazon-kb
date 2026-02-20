from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict

from core.models import KnowledgeBase, QueryRequest, QueryResponse
from core.ports import KnowledgeBaseProvider
from adapter.AmazonKnowledgeBaseProvider import AmazonKnowledgeBaseProvider

router = APIRouter()

def get_provider() -> KnowledgeBaseProvider:
    return AmazonKnowledgeBaseProvider()

@router.get("/knowledge-bases", response_model=Dict[str, KnowledgeBase])
async def list_knowledge_bases(provider: KnowledgeBaseProvider = Depends(get_provider)):
    try:
        return await provider.list_knowledge_bases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, provider: KnowledgeBaseProvider = Depends(get_provider)):
    try:
        # If knowledge_base_id is missing, we could try to find a default or search all?
        # For now, let's assume it's required for the Amazon provider.
        if not request.knowledge_base_id:
             # Try to list and pick the first one? Or just error?
             # Let's error for clarity.
             raise HTTPException(status_code=400, detail="knowledge_base_id is required for Amazon Knowledge Base queries.")
             
        return await provider.query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
