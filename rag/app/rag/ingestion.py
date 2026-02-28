import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def limpiar_texto(texto: str) -> str:
    """Limpia el texto extraído del PDF eliminando ruido común."""
    if not texto:
        return ""
    
    # 1. Eliminar ruido típico de la web de SUIN-Juriscol
    ruido_suin = [
        r'\[Mostrar\]',
        r'Responder Encuesta',
        r'Descargar en Word',
        r'Compartir este documento',
        r'Lectura de voz',
        r'Ayúdanos a mejorar',
        r'Ir al portal SUIN-Juriscol',
        r'Sistema Único de Información Normativa',
        r'Guardar en PDF o imprimir la norma',
        r'Inscripciones abiertas'
    ]
    for patron in ruido_suin:
        texto = re.sub(patron, '', texto, flags=re.IGNORECASE)
        
    # 2. Eliminar fechas de impresión web (ej: 23/2/26, 9:10 p.m.)
    texto = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[a-p]\.m\.', '', texto)
    
    # 3. Eliminar URLs
    texto = re.sub(r'https?://\S+', '', texto)
    # 4. ELIMINAR CARACTERES RAROS / ICONOS DE TEXTO
    # Solo permitimos: Letras (incluyendo acentos y ñ), números, espacios y puntuación básica
    texto = re.sub(r'[^\w\s.,;:!?()"\-áéíóúÁÉÍÓÚñÑüÜ¿¡]', '', texto)
    
    # 5. Reemplazar múltiples saltos de línea por uno solo
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # 6. Reemplazar múltiples espacios por un solo espacio
    texto = re.sub(r' {2,}', ' ', texto)
    # 7. Eliminar caracteres nulos extraños que a veces vienen en PDFs viejos
    texto = texto.replace('\x00', '')
    # 8. Quitar espacios en blanco al inicio y al final
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
    """
    Crea el índice vectorial usando Google text-embedding-004.
    Este modelo es significativamente más potente que MiniLM-L12:
    - 768 dimensiones vs 384
    - Mejor comprensión semántica en español
    - Mejor manejo de terminología legal
    """
    # Google embedding-001 - Modelo estable de Google
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        raise ValueError("GOOGLE_API_KEY no está configurada en el entorno")
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
        google_api_key=google_key
    )
    print("✅ Usando Google embedding-001 para embeddings")
    
    # Crear y persistir la base de datos Chroma localmente
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./db_chroma"
    )
    
    return vectorstore