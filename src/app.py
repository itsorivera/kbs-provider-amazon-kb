from fastapi import FastAPI
from src.adapter.rest.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="KBS Provider Amazon KB",
        description="Provider for Amazon Bedrock Knowledge Bases",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    app.include_router(router)
    
    return app

app = create_app()