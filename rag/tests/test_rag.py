import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Obtener la ruta raíz del proyecto (rag/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# IMPORTANTE: Cargar variables de entorno ANTES de importar módulos que usen API keys
load_dotenv(os.path.join(PROJECT_ROOT, "app", "rag", ".env"))

# 1. Importamos TU función real desde el archivo retriever.py
from app.rag.retriever import recuperar_contexto_dinamico 

# 2. Definimos la función formateadora que acabamos de completar
def formatear_documentos_para_gemini(documentos_recuperados) -> str:
    texto_final = "CONTEXTO RECUPERADO DE LA BASE DE DATOS LEGAL:\n\n"
    for i, doc in enumerate(documentos_recuperados):
        contenido = doc.page_content
        doc_id = doc.metadata.get('doc_id', 'Documento Desconocido')
        pagina = doc.metadata.get('page', 'Sin página')
        
        texto_final += f"--- FRAGMENTO {i+1} ---\n"
        texto_final += f"Cita: Documento '{doc_id}', Página {pagina}\n"
        texto_final += f"Texto: {contenido}\n\n"
    return texto_final

def simular_flujo_rag():
    print("🔌 Conectando a la base de datos ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    db_path = os.path.join(PROJECT_ROOT, "db_chroma")
    vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
    
    # Consultas de prueba
    consultas = [
        "¿A cuántos días de vacaciones remuneradas tiene derecho un trabajador?",
        "¿Cuáles son las justas causas para terminar un contrato laboral?"
    ]
    
    for pregunta in consultas:
        print(f"\n" + "="*50)
        print(f"👤 USUARIO: '{pregunta}'")
        print("="*50)
        
        # PASO A: Ejecutamos tu retriever (Groq decide el K y busca)
        # Nota: Asegúrate de que tu función recuperar_contexto_dinamico reciba el vectorstore como parámetro
        print("🔍 Ejecutando Retriever (Groq + ChromaDB)...")
        documentos = recuperar_contexto_dinamico(pregunta, vectorstore)
        
        print(f"✅ Se recuperaron {len(documentos)} fragmentos.")
        
        # PASO B: Formateamos el texto para Gemini
        texto_formateado = formatear_documentos_para_gemini(documentos)
        
        print("\n📦 PAQUETE FINAL QUE RECIBIRÁ GEMINI EN SU PROMPT:")
        print(texto_formateado)

if __name__ == "__main__":
    simular_flujo_rag()