import boto3
from typing import Dict, List, Optional
from loguru import logger
import json
import traceback
from core.ports import KnowledgeBaseProvider
from core.models import KnowledgeBase, DataSource, QueryRequest, QueryResponse, SearchResult
from config import settings

class AmazonKnowledgeBaseProvider(KnowledgeBaseProvider):
    def __init__(self):
        self.agent_client = self._get_client('bedrock-agent')
        self.agent_runtime_client = self._get_client('bedrock-agent-runtime')
        self.tag_key = settings.KNOWLEDGE_BASE_TAG_KEY

    def _get_client(self, service_name: str):
        if settings.AWS_PROFILE:
            session = boto3.Session(profile_name=settings.AWS_PROFILE)
            return session.client(service_name, region_name=settings.AWS_REGION)
        return boto3.client(service_name, region_name=settings.AWS_REGION)

    async def list_knowledge_bases(self) -> Dict[str, KnowledgeBase]:
        result = {}
        
        # Collect KBs
        paginator = self.agent_client.get_paginator('list_knowledge_bases')
        for page in paginator.paginate():
            for kb_summary in page.get('knowledgeBaseSummaries', []):
                kb_id = kb_summary.get('knowledgeBaseId')
                kb_name = kb_summary.get('name')
                
                # Check tags
                try:
                    kb_details = self.agent_client.get_knowledge_base(knowledgeBaseId=kb_id)
                    kb_arn = kb_details.get('knowledgeBase', {}).get('knowledgeBaseArn')
                    tags = self.agent_client.list_tags_for_resource(resourceArn=kb_arn).get('tags', {})
                    
                    if self.tag_key in tags and tags[self.tag_key] == 'true':
                        # Get data sources
                        data_sources = self._get_data_sources(kb_id)
                        
                        result[kb_id] = KnowledgeBase(
                            id=kb_id,
                            name=kb_name,
                            description=kb_summary.get('description', ''),
                            data_sources=data_sources
                        )
                except Exception as e:
                    logger.error(f"Error processing KB {kb_id}: {e}")
                    continue
                    
        return result

    def _get_data_sources(self, kb_id: str) -> List[DataSource]:
        data_sources = []
        paginator = self.agent_client.get_paginator('list_data_sources')
        try:
            for page in paginator.paginate(knowledgeBaseId=kb_id):
                for ds in page.get('dataSourceSummaries', []):
                    data_sources.append(DataSource(
                        id=ds.get('dataSourceId'),
                        name=ds.get('name')
                    ))
        except Exception as e:
            logger.error(f"Error listing data sources for KB {kb_id}: {e}")
            
        return data_sources

    async def retrieve(self, request: QueryRequest) -> QueryResponse:
        if not request.knowledge_base_id:
             # In a real scenario we might query all KBs, but for now we require ID or handle it upstream
             # Ideally the Gateway handles the "which provider" part. 
             # If this provider is called, it expects a KB ID that belongs to it.
             # However, the user might send a query without ID if they want to search "all amazon KBs" 
             # (though that would be slow). 
             # For now, let's assume the ID is passed or we pick the first one?
             # The contract says POST /query {"query": "string"}, so the ID might be inferred or we search all.
             # But the Amazon Retrieves API requires a KB ID.
             # The README says: POST /query Recibe {"query": "string"} y devuelve {"answer": "string"}.
             # If the gateway calls this service, and this service manages MULTIPLE KBs, 
             # we probably need to know WHICH one to query, OR query them all.
             # Given the "Gateway" context, the Gateway likely knows which KB to query 
             # OR this service exposes all Amazon KBs as a single endpoint.
             # Let's inspect retrieval.py again. It takes knowledge_base_id.
             
             # If no ID is provided, we might need to search all of them (expensive) or return error.
             # Let's check if the request model allows optional ID. Yes.
             pass

        if not request.knowledge_base_id:
             raise ValueError("knowledge_base_id is required for Amazon KB query")

        request_config = {
            'vectorSearchConfiguration': {
                'numberOfResults': request.num_results,
            }
        }

        if request.data_source_ids:
             request_config['vectorSearchConfiguration']['filter'] = {
                'in': {
                    'key': 'x-amz-bedrock-kb-data-source-id',
                    'value': request.data_source_ids
                }
            }
            
        if request.reranking:
            # Simple mapping for now, can be expanded
            model_arn = f'arn:aws:bedrock:{settings.AWS_REGION}::foundation-model/amazon.rerank-v1:0'
            request_config['vectorSearchConfiguration']['rerankingConfiguration'] = {
                'type': 'BEDROCK_RERANKING_MODEL',
                'bedrockRerankingConfiguration': {
                    'modelConfiguration': {
                        'modelArn': model_arn
                    }
                }
            }

        response = self.agent_runtime_client.retrieve(
            knowledgeBaseId=request.knowledge_base_id,
            retrievalQuery={'text': request.query},
            retrievalConfiguration=request_config
        )

        results = []
        for result in response.get('retrievalResults', []):
             if result['content'].get('type') != 'IMAGE':
                results.append(SearchResult(
                    content=result['content'],
                    location=result.get('location', {}),
                    score=result.get('score')
                ))
        
        formatted_answer = "\n\n".join([json.dumps(r.model_dump(), default=str) for r in results])
        
        return QueryResponse(
            results=results,
            answer=formatted_answer
        )

    async def retrieve_and_generate(self, request: QueryRequest) -> QueryResponse:
        if not request.knowledge_base_id:
             raise ValueError("knowledge_base_id is required for Amazon KB query and generate")

        # 1. Build retrieveAndGenerateConfiguration
        # The API structure for retrieveAndGenerate is:
        # {
        #   "input": { "text": "string" },
        #   "retrieveAndGenerateConfiguration": {
        #       "type": "KNOWLEDGE_BASE",
        #       "knowledgeBaseConfiguration": {
        #           "knowledgeBaseId": "string",
        #           "modelArn": "string", # Optional, if using a specific model
        #           "retrievalConfiguration": { ... } # Optional
        #       }
        #   }
        # }
        
        #TODO: We need a model ARN for generation. Parameter on the request? Or default to a specific one? 
        # Ideally this comes from settings or request, but let's default to a popular one or one from settings if available.
        # Check if we have a default model arn in settings, otherwise use a hardcoded default (e.g. Claude 3 or Titan)
        # For now, let's assume 'anthropic.claude-3-sonnet-20240229-v1:0' or similar if not in settings.
        # Actually, let's look at config.py to see if there is a MODEL_ARN.
        model_arn = getattr(settings, 'GENERATION_MODEL_ARN', 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0')

        kb_config = {
            'knowledgeBaseId': request.knowledge_base_id,
            'modelArn': model_arn,
        }

        # Add retrieval configuration if needed (e.g. number of results)
        if request.num_results:
             kb_config['retrievalConfiguration'] = {
                'vectorSearchConfiguration': {
                    'numberOfResults': request.num_results
                }
             }
             
        # Add filter if data_source_ids are present
        if request.data_source_ids:
            if 'retrievalConfiguration' not in kb_config:
                 kb_config['retrievalConfiguration'] = {'vectorSearchConfiguration': {}}
            
            kb_config['retrievalConfiguration']['vectorSearchConfiguration']['filter'] = {
                'in': {
                    'key': 'x-amz-bedrock-kb-data-source-id',
                    'value': request.data_source_ids
                }
            }

        # 2. Call the API
        try:
            response = self.agent_runtime_client.retrieve_and_generate(
                input={'text': request.query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': kb_config
                }
            )
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error in retrieve_and_generate: {e}")
            raise

        # 3. Parse the response

        answer_text = response.get('output', {}).get('text', '')
        
        results = []
        citations = response.get('citations', [])
        for citation in citations:
            for ref in citation.get('retrievedReferences', []):
                 # Map to SearchResult
                 # Note: retrieve_and_generate structure is slightly different from retrieve
                 content = ref.get('content', {})
                 location = ref.get('location', {})
                 metadata = ref.get('metadata', {})
                 
                 api_content = {
                     'text': content.get('text'),
                     'metadata': metadata
                 }

                 results.append(SearchResult(
                     content=api_content,
                     location=location,
                     score=None # No score provided in retrieveAndGenerate references usually
                 ))

        return QueryResponse(
            results=results,
            answer=answer_text
        )
