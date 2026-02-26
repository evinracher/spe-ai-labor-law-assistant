import os
# from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Comentado - no se usa actualmente
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma # Usamos el paquete actualizado de Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def limpiar_texto(texto: str) -> str:
    """Limpia el texto extraído del PDF eliminando ruido común."""
    if not texto:
        return ""
    # 1. Reemplazar múltiples saltos de línea por uno solo
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # 2. Reemplazar múltiples espacios por un solo espacio
    texto = re.sub(r' {2,}', ' ', texto)
    # 3. Eliminar caracteres nulos extraños que a veces vienen en PDFs viejos
    texto = texto.replace('\x00', '')
    # 4. Quitar espacios en blanco al inicio y al final
    return texto.strip()

def procesar_pdf(ruta_archivo):
    try:
        # Paso 1: Carga
        loader = PyPDFLoader(ruta_archivo)
        documentos = loader.load()
        # Limpiar el texto de cada documento
        for doc in documentos:
            doc.page_content = limpiar_texto(doc.page_content)
            
        # Paso 2: Configuración del fragmentador
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=150,
            separators=["\nARTÍCULO", "\nPARÁGRAFO", "\nCAPÍTULO", "\nTÍTULO", "\n\n", "\n", " ", ""]
        )
        
        # Paso 3: División
        chunks = text_splitter.split_documents(documentos)
        
        # Paso 4: Metadatos para trazabilidad
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = f"chunk_{i}"
            chunk.metadata['doc_id'] = chunk.metadata.get('source', 'documento_desconocido')
            
        return chunks
    except Exception as e:
        print(f"Error al procesar el PDF {ruta_archivo} con error: {e}")
        return []


# Asumimos que 'chunks' es la lista que retornó nuestra función anterior
def crear_indice_vectorial(chunks):
    # 1. Definir el modelo de embeddings de Google
    # Nota: Requiere tener os.environ["GOOGLE_API_KEY"] configurado
    #google_key = os.getenv("GOOGLE_API_KEY")
    #embeddings = GoogleGenerativeAIEmbeddings(
    #    model="models/embedding-001",
    #    google_api_key=google_key
    #)
    
    # Alternativamente, puedes usar un modelo de HuggingFace local (sin necesidad de API Key)
    model = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = HuggingFaceEmbeddings(model_name=model)
    
    # 2. Crear y persistir la base de datos Chroma localmente
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./db_chroma" # Se guardará en la carpeta que definimos en la arquitectura
    )
    
    return vectorstore