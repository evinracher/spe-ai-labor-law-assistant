from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.core.config import settings


# 1. Definimos la estructura exacta que queremos que devuelva Groq (solo un número)
class KSelector(BaseModel):
    k_value: int = Field(description="Number of fragments to retrieve, between 1 and 10")


def recuperar_contexto_dinamico(pregunta: str, vectorstore):
    # 2. Instanciamos Groq (requiere GROQ_API_KEY en tu .env)
    llm_groq = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=settings.GROQ_API_KEY)

    # Forzamos a que la salida sea un objeto estructurado (JSON con la llave 'k_value')
    llm_estructurado = llm_groq.with_structured_output(KSelector)

    # 3. Prompt para decidir el K
    prompt = PromptTemplate.from_template(
        "You are a legal expert. Given this user query: '{pregunta}'\n"
        "Determine how many law fragments (between 1 and 10) we need to retrieve "
        "to fully answer it. If it is very specific, choose 2 or 4. "
        "If it is very broad, choose 8 or 10."
    )

    # 4. Ejecutamos la cadena para obtener K
    cadena_k = prompt | llm_estructurado
    resultado_k = cadena_k.invoke({"pregunta": pregunta})
    k_dinamico = resultado_k.k_value

    print(
        f"Buscando {k_dinamico} fragmentos para la consulta (estrategia: {settings.RETRIEVAL_STRATEGY})..."
    )

    # 5. Hacemos la búsqueda real en la base vectorial.
    # MMR (Maximal Marginal Relevance) re-ranks a larger candidate pool (fetch_k) so that
    # the final k documents are both relevant to the query AND diverse among themselves,
    # avoiding near-duplicate passages in the retrieved context.
    if settings.RETRIEVAL_STRATEGY == "mmr":
        documentos_recuperados = vectorstore.max_marginal_relevance_search(
            pregunta,
            k=k_dinamico,
            fetch_k=max(k_dinamico * 4, settings.MMR_FETCH_K),
            lambda_mult=settings.MMR_LAMBDA,
        )
    else:
        documentos_recuperados = vectorstore.similarity_search(pregunta, k=k_dinamico)

    return documentos_recuperados


def formatear_documentos_para_gemini(documentos_recuperados) -> str:
    """Convierte los documentos de ChromaDB en un string formateado con citas."""
    texto_final = "CONTEXTO RECUPERADO DE LA BASE DE DATOS LEGAL:\n\n"

    for i, doc in enumerate(documentos_recuperados):
        # Extraemos la información del objeto
        contenido = doc.page_content
        doc_id = doc.metadata.get("doc_id", "Documento Desconocido")
        pagina = doc.metadata.get("page", "Sin página")
        chunk_id = doc.metadata.get("chunk_id", "Sin ID")

        # Usa estas 4 variables (contenido, doc_id, pagina, chunk_id) para armar
        # un bloque de texto ordenado y súmalo a 'texto_final'.

        texto_final += f"--- FRAGMENTO {i+1} ---\n"
        texto_final += f"Cita: {doc_id}, Página: {pagina}, Fragmento: {chunk_id}\n"
        texto_final += f"Texto: {contenido}\n\n"

    return texto_final
