import chromadb
from app.core.config import settings

def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(settings.CHROMA_DIR))