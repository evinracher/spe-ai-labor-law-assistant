import os
import glob
from dotenv import load_dotenv

# 1. Cargar las API Keys desde el archivo .env
load_dotenv()

# Obtener el directorio base del proyecto (rag/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))

# Añadir el proyecto al path
import sys
sys.path.insert(0, PROJECT_ROOT)
print("Path actual:", os.getcwd())
print("Raíz del proyecto:", PROJECT_ROOT)

# 2. Importar tus funciones
from app.rag.ingestion import procesar_pdf, crear_indice_vectorial

def main():
    # Ruta absoluta a la carpeta data
    ruta_datos = os.path.join(PROJECT_ROOT, "app", "data")
    print(f"Buscando archivos PDF en: {ruta_datos}")
    todos_los_chunks = []
    
    print("Iniciando la lectura de PDFs...")
    # Buscamos todos los archivos PDF en la carpeta
    archivos_pdf = glob.glob(os.path.join(ruta_datos, "*.pdf"))
    
    for archivo in archivos_pdf:
        print(f"Procesando: {archivo}")
        chunks = procesar_pdf(archivo)
        todos_los_chunks.extend(chunks)
        
    print(f"Total de fragmentos (chunks) generados: {len(todos_los_chunks)}")
    
    print("Generando embeddings y guardando en ChromaDB...")
    # Esto creará la carpeta ./db con tu base de datos
    vectorstore = crear_indice_vectorial(todos_los_chunks)
    
    print("¡Base de datos vectorial creada con éxito!")

if __name__ == "__main__":
    main()