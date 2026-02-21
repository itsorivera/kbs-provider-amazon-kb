from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict

from src.core.models import KnowledgeBase, QueryRequest, QueryResponse, ListKnowledgeBasesResponse
from src.core.ports import KnowledgeBaseProvider
from src.adapter.AmazonKnowledgeBaseProvider import AmazonKnowledgeBaseProvider

router = APIRouter()

def get_provider() -> KnowledgeBaseProvider:
    return AmazonKnowledgeBaseProvider()

@router.get("/knowledge-bases", response_model=ListKnowledgeBasesResponse)
async def list_knowledge_bases(
    next_token: Optional[str] = None,
    provider: KnowledgeBaseProvider = Depends(get_provider)
):
    try:
        return await provider.list_knowledge_bases(next_token=next_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrieve", response_model=QueryResponse)
async def retrieve(request: QueryRequest, provider: KnowledgeBaseProvider = Depends(get_provider)):
    try:
        if not request.knowledge_base_id:
             raise HTTPException(status_code=400, detail="knowledge_base_id is required for Amazon Knowledge Base queries.")
             
        return await provider.retrieve(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrieve-and-generate", response_model=QueryResponse)
async def retrieve_and_generate(request: QueryRequest, provider: KnowledgeBaseProvider = Depends(get_provider)):
    try:
        if not request.knowledge_base_id:
             raise HTTPException(status_code=400, detail="knowledge_base_id is required for Amazon Knowledge Base queries.")
             
        return await provider.retrieve_and_generate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
