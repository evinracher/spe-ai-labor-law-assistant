"""
run_ingestion_test.py
---------------------
Lightweight ingestion pipeline for local development and testing.

Key differences from the production pipeline (run_ingestion.py):
- Reads PDFs only from app/data/test/ (a small, curated subset).
- Uses RecursiveCharacterTextSplitter instead of SemanticChunker,
  which avoids Gemini API calls during chunking and runs offline/fast.
- Writes the vector index to ./db_chroma_test (separate from production).

Usage
-----
# From the rag/ directory with the virtual environment activated:
python -m app.rag.pipelines.run_ingestion_test

# Or via Makefile:
make ingest-test

Then point the server at the test database by setting in .env:
  CHROMA_DIR=./db_chroma_test
"""

import glob
import os
import sys
import time

from dotenv import load_dotenv

# ── Path bootstrap ────────────────────────────────────────────────────────────
# Must happen before any app.* imports so the package is discoverable.
load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# ── Imports after path bootstrap ──────────────────────────────────────────────
# ruff: noqa: E402  (imports intentionally after sys.path modification)
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.ingestion import limpiar_texto

# ── Constants ─────────────────────────────────────────────────────────────────
TEST_DATA_DIR = os.path.join(PROJECT_ROOT, "app", "data", "test")
TEST_CHROMA_DIR = os.path.join(PROJECT_ROOT, "db_chroma_test")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SEPARATORS = ["\nARTÍCULO", "\nPARÁGRAFO", "\nCAPÍTULO", "\nTÍTULO", "\n\n", "\n", " ", ""]


def procesar_pdf_rapido(ruta_archivo: str) -> list:
    """
    Load and chunk a single PDF using RecursiveCharacterTextSplitter.
    This is much faster than SemanticChunker because it requires no API calls.
    """
    print(f"  Cargando: {os.path.basename(ruta_archivo)}")
    loader = PyPDFLoader(ruta_archivo)
    documentos = loader.load()

    for doc in documentos:
        doc.page_content = limpiar_texto(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )
    chunks = splitter.split_documents(documentos)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i}"
        chunk.metadata["doc_id"] = chunk.metadata.get("source", "documento_desconocido")

    print(f"  ✅ {len(chunks)} fragmentos generados.")
    return chunks


def crear_indice_vectorial_test(chunks: list) -> None:
    """Embed chunks con Google en lotes para evitar el error 429."""
    chunks_validos = [c for c in chunks if c.page_content and c.page_content.strip()]
    total = len(chunks_validos)
    
    google_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
        google_api_key=google_key,
    )

    # Configuración de lotes (Batches)
    # Enviamos 80 para estar seguros bajo el límite de 100
    batch_size = 80 
    print(f"🚀 Procesando {total} chunks en lotes de {batch_size}...")

    for i in range(0, total, batch_size):
        batch = chunks_validos[i : i + batch_size]
        
        # En el primer lote creamos la DB, en los siguientes añadimos (add_documents)
        if i == 0:
            vector_db = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=TEST_CHROMA_DIR,
            )
        else:
            vector_db.add_documents(documents=batch)
        
        progreso = min(i + batch_size, total)
        print(f"✅ Progreso: {progreso}/{total} guardados.")

        # Si aún quedan lotes, esperamos 60 segundos para resetear la cuota de Google
        if progreso < total:
            print("⏳ Esperando 60 segundos para evitar bloqueo de cuota de Google...")
            time.sleep(60)

def main() -> None:
    print(f"📂 Directorio de test: {TEST_DATA_DIR}")
    print(f"💾 Destino ChromaDB:   {TEST_CHROMA_DIR}\n")

    archivos_pdf = glob.glob(os.path.join(TEST_DATA_DIR, "*.pdf"))
    archivos_pdf += glob.glob(os.path.join(TEST_DATA_DIR, "*.PDF"))

    if not archivos_pdf:
        print("⚠️  No se encontraron archivos PDF en el directorio de test.")
        print("   Coloca al menos un PDF en: " + TEST_DATA_DIR)
        sys.exit(1)

    print(f"📄 Archivos encontrados: {len(archivos_pdf)}")
    todos_los_chunks: list = []

    for archivo in archivos_pdf:
        chunks = procesar_pdf_rapido(archivo)
        todos_los_chunks.extend(chunks)

    print(f"\n📊 Total de fragmentos generados: {len(todos_los_chunks)}")
    print("🔗 Generando embeddings y guardando en ChromaDB de test...")

    crear_indice_vectorial_test(todos_los_chunks)

    print("\n✅ Base de datos vectorial de TEST creada en: " + TEST_CHROMA_DIR)
    print(
        "\nPara usar esta base al levantar el servidor, agrega a tu .env:\n"
        "  CHROMA_DIR=./db_chroma_test\n"
    )


if __name__ == "__main__":
    main()
