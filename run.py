import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("src.app:app", 
                host=os.getenv("UVICORN_HOST", "127.0.0.1"),
                port=int(os.getenv("UVICORN_PORT", 8000)),
                reload=os.getenv("UVICORN_RELOAD", "true").lower() == "true"
                )