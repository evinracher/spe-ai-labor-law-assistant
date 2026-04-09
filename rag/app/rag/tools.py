from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langsmith import traceable

from app.core.config import settings

if TYPE_CHECKING:
    pass

# ====================================================================
# Module-level Vector DB Initialization
# ====================================================================

_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_RESET = "\033[0m"

# Project paths
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Resolve CHROMA_DIR relative to the project root when it is not absolute
_chroma_dir = settings.CHROMA_DIR
if not _chroma_dir.is_absolute():
    _chroma_dir = (Path(_PROJECT_ROOT) / _chroma_dir).resolve()
_DB_CHROMA_PATH = str(_chroma_dir)

# Vector Database (shared instance) - Google embedding-001
_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="RETRIEVAL_DOCUMENT",
    google_api_key=settings.GOOGLE_API_KEY,
)
_vectorstore = Chroma(persist_directory=_DB_CHROMA_PATH, embedding_function=_embeddings)

# Leyes principales y su estado de vigencia
LAW_VIGENCY_DB = {
    "ley 100 de 1993": {"vigente": True, "modificada_por": ["Ley 797 de 2003", "Ley 860 de 2003"]},
    "codigo sustantivo del trabajo": {"vigente": True, "modificada_por": ["Múltiples reformas"]},
    "ley 50 de 1990": {"vigente": True, "modificada_por": []},
    "decreto 1072 de 2015": {"vigente": True, "modificada_por": ["Decreto 1563 de 2016"]},
    "ley 789 de 2002": {"vigente": True, "modificada_por": []},
    "ley 1010 de 2006": {"vigente": True, "modificada_por": []},  # Acoso laboral
    "ley 1562 de 2012": {"vigente": True, "modificada_por": []},  # Riesgos laborales
    "ley 2101 de 2021": {"vigente": True, "modificada_por": []},  # Reducción jornada laboral
}


@tool
def search_by_law_number(law_identifier: str, max_results: int = 5) -> dict:
    """
    Busca fragmentos de una ley específica por su número o nombre.

    A diferencia de la búsqueda semántica, esta herramienta busca
    directamente en los metadatos del documento por coincidencia exacta
    del identificador de ley.

    Args:
        law_identifier: Número o nombre de ley (ej: "Ley 100", "Decreto 1072", "CST")
        max_results: Máximo de fragmentos a retornar (default: 5)

    Returns:
        Dictionary con fragmentos encontrados y metadatos

    Casos de uso:
        - "Dame los artículos de la Ley 100 de 1993"
        - "Busca en el Decreto 1072"
        - "Qué dice el Código Sustantivo del Trabajo"
    """
    print(f"{_GREEN}[TOOL 1] search_by_law_number - Buscando: {law_identifier}{_RESET}")

    try:
        # Normalizar el identificador
        normalized = law_identifier.lower().strip()

        # Obtener todos los documentos y filtrar por doc_id
        all_docs = _vectorstore.get(include=["documents", "metadatas"])

        matching_docs = []
        if all_docs and all_docs.get("metadatas"):
            for i, metadata in enumerate(all_docs["metadatas"]):
                doc_id = metadata.get("doc_id", "").lower()
                # Buscar coincidencia parcial en el nombre del documento
                if normalized in doc_id or any(term in doc_id for term in normalized.split()):
                    matching_docs.append(
                        {
                            "content": all_docs["documents"][i][:500] + "...",
                            "metadata": metadata,
                            "chunk_id": metadata.get("chunk_id", "N/A"),
                            "page": metadata.get("page", "N/A"),
                        }
                    )
                    if len(matching_docs) >= max_results:
                        break

        output = {
            "law_identifier": law_identifier,
            "normalized_query": normalized,
            "total_found": len(matching_docs),
            "documents": matching_docs,
            "source": "chroma_metadata_filter",
        }

        print(f"{_GREEN}[TOOL 1] search_by_law_number - Encontrados: {len(matching_docs)}{_RESET}")
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 1] search_by_law_number - ERROR: {e!s}{_RESET}")
        return {
            "law_identifier": law_identifier,
            "total_found": 0,
            "documents": [],
            "error": str(e),
        }


@tool
def get_article_text(article_number: str, law_name: str = "") -> dict:
    """
    Obtiene el texto completo de un artículo específico de una ley.

    Usa búsqueda semántica optimizada para encontrar artículos exactos,
    combinando el número de artículo con el contexto de la ley.

    Args:
        article_number: Número del artículo (ej: "64", "127", "306")
        law_name: Nombre de la ley (opcional, ej: "Código Sustantivo del Trabajo")

    Returns:
        Dictionary con el texto del artículo y metadatos

    Casos de uso:
        - "Artículo 64 del CST" (indemnización por despido)
        - "Artículo 127 del Código Sustantivo" (definición de salario)
        - "Dame el artículo 306" (prima de servicios)
    """
    print(
        f"{_GREEN}[TOOL 2] get_article_text - Art. {article_number} de {law_name or 'cualquier ley'}{_RESET}"
    )

    try:
        # Construir múltiples queries para mejorar recall
        queries = [
            f"ARTÍCULO {article_number}",
            f"articulo {article_number} {law_name}" if law_name else f"articulo {article_number}",
        ]

        # Buscar con múltiples queries y k más alto
        all_results = []
        for query in queries:
            results = _vectorstore.similarity_search(query, k=10)
            all_results.extend(results)

        # Filtrar resultados que contengan el número de artículo exacto
        article_pattern = rf"ART[ÍI]CULO\s*{article_number}[.\s\-\:]"
        matching_results = []
        seen_chunks = set()

        for doc in all_results:
            chunk_id = doc.metadata.get("chunk_id", "")
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            # Verificar si el artículo está en el contenido
            if re.search(article_pattern, doc.page_content, re.IGNORECASE):
                # Si se especificó ley, filtrar por documento
                if law_name:
                    doc_id_lower = doc.metadata.get("doc_id", "").lower()
                    if not any(term in doc_id_lower for term in law_name.lower().split()):
                        continue

                matching_results.append(
                    {
                        "content": doc.page_content,
                        "source": doc.metadata.get("doc_id", "Unknown"),
                        "page": doc.metadata.get("page"),
                        "chunk_id": chunk_id,
                    }
                )

        # Si no hay coincidencia exacta, intentar búsqueda más amplia
        if not matching_results:
            # Buscar en todos los documentos con filtro de metadatos
            all_docs = _vectorstore.get(include=["documents", "metadatas"])
            for i, content in enumerate(all_docs.get("documents", [])):
                if re.search(article_pattern, content, re.IGNORECASE):
                    metadata = all_docs["metadatas"][i]
                    if law_name:
                        doc_id_lower = metadata.get("doc_id", "").lower()
                        if not any(term in doc_id_lower for term in law_name.lower().split()):
                            continue
                    matching_results.append(
                        {
                            "content": content,
                            "source": metadata.get("doc_id", "Unknown"),
                            "page": metadata.get("page"),
                            "chunk_id": metadata.get("chunk_id", "N/A"),
                        }
                    )
                    if len(matching_results) >= 3:
                        break

        output = {
            "article_number": article_number,
            "law_name": law_name or "No especificada",
            "found": len(matching_results) > 0,
            "results": matching_results[:3],  # Máximo 3 resultados
            "search_query_used": queries[0],
        }

        print(
            f"{_GREEN}[TOOL 2] get_article_text - Encontrado: {output['found']} ({len(matching_results)} chunks){_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 2] get_article_text - ERROR: {e!s}{_RESET}")
        return {
            "article_number": article_number,
            "law_name": law_name,
            "found": False,
            "results": [],
            "error": str(e),
        }


@tool
def list_laws_by_topic(topic: str, max_results: int = 10) -> dict:
    """
    Lista las leyes y decretos relacionados con un tema específico.

    Realiza búsqueda semántica y agrupa los resultados por documento
    fuente, proporcionando un resumen de qué leyes tratan el tema.

    Args:
        topic: Tema a buscar (ej: "despido", "vacaciones", "pensiones")
        max_results: Máximo de leyes únicas a retornar (default: 10)

    Returns:
        Dictionary con lista de leyes relacionadas al tema

    Casos de uso:
        - "Qué leyes hablan sobre pensiones"
        - "Normatividad sobre acoso laboral"
        - "Leyes de maternidad y paternidad"
    """
    print(f"{_GREEN}[TOOL 3] list_laws_by_topic - Tema: {topic}{_RESET}")

    try:
        # Búsqueda semántica amplia
        results = _vectorstore.similarity_search(topic, k=20)

        # Agrupar por documento fuente
        laws_found = {}
        for doc in results:
            doc_id = doc.metadata.get("doc_id", "Unknown")
            if doc_id not in laws_found:
                laws_found[doc_id] = {
                    "doc_id": doc_id,
                    "mentions": 1,
                    "sample_content": doc.page_content[:300] + "...",
                    "pages_found": [doc.metadata.get("page")],
                }
            else:
                laws_found[doc_id]["mentions"] += 1
                page = doc.metadata.get("page")
                if page and page not in laws_found[doc_id]["pages_found"]:
                    laws_found[doc_id]["pages_found"].append(page)

        # Ordenar por número de menciones (relevancia implícita)
        sorted_laws = sorted(laws_found.values(), key=lambda x: x["mentions"], reverse=True)[
            :max_results
        ]

        output = {
            "topic": topic,
            "total_laws_found": len(sorted_laws),
            "laws": sorted_laws,
            "search_depth": 20,
        }

        print(
            f"{_GREEN}[TOOL 3] list_laws_by_topic - Leyes encontradas: {len(sorted_laws)}{_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 3] list_laws_by_topic - ERROR: {e!s}{_RESET}")
        return {"topic": topic, "total_laws_found": 0, "laws": [], "error": str(e)}



@tool
def get_document_metadata(doc_id: str) -> dict:
    """
    Obtiene los metadatos completos de un documento sin cargar el contenido.

    Útil para obtener información sobre el documento (páginas, chunks,
    fecha, etc.) sin consumir tokens con el contenido completo.

    Args:
        doc_id: Identificador del documento (path o nombre)

    Returns:
        Dictionary con metadatos del documento

    Casos de uso:
        - Verificar de qué documento proviene una citación
        - Conocer la estructura de un documento antes de leerlo
        - Obtener información de trazabilidad
    """
    print(f"{_GREEN}[TOOL 4] get_document_metadata - doc_id: {doc_id}{_RESET}")

    try:
        # Obtener todos los chunks del documento
        all_data = _vectorstore.get(include=["metadatas"])

        doc_chunks = []
        pages_set = set()

        if all_data and all_data.get("metadatas"):
            for metadata in all_data["metadatas"]:
                if doc_id.lower() in metadata.get("doc_id", "").lower():
                    doc_chunks.append(metadata)
                    if metadata.get("page"):
                        pages_set.add(metadata["page"])

        if not doc_chunks:
            return {
                "doc_id": doc_id,
                "found": False,
                "error": "Documento no encontrado en la base vectorial",
            }

        output = {
            "doc_id": doc_id,
            "found": True,
            "total_chunks": len(doc_chunks),
            "total_pages": len(pages_set),
            "pages": sorted(list(pages_set)) if pages_set else [],
            "sample_metadata": doc_chunks[0] if doc_chunks else {},
            "chunk_ids": [c.get("chunk_id") for c in doc_chunks[:10]],  # Primeros 10
        }

        print(
            f"{_GREEN}[TOOL 4] get_document_metadata - Chunks: {len(doc_chunks)}, Pages: {len(pages_set)}{_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 4] get_document_metadata - ERROR: {e!s}{_RESET}")
        return {"doc_id": doc_id, "found": False, "error": str(e)}



@tool
def check_law_vigency(law_name: str) -> dict:
    """
    Verifica si una ley o decreto está vigente y si ha sido modificado.

    Consulta una base de datos de referencia con el estado de las
    principales normas laborales colombianas.

    Args:
        law_name: Nombre de la ley (ej: "Ley 100 de 1993", "Decreto 1072")

    Returns:
        Dictionary con estado de vigencia y modificaciones

    Casos de uso:
        - "¿La Ley 100 de 1993 sigue vigente?"
        - "¿El Decreto 1072 ha sido modificado?"
        - Validar que una citación no sea de ley derogada
    """
    print(f"{_GREEN}[TOOL 5] check_law_vigency - Consultando: {law_name}{_RESET}")

    try:
        normalized = law_name.lower().strip()

        # Buscar en la base de vigencias
        found_law = None
        for key, value in LAW_VIGENCY_DB.items():
            if key in normalized or normalized in key:
                found_law = {"name": key, **value}
                break

        if found_law:
            output = {
                "law_name": law_name,
                "found_in_db": True,
                "vigente": found_law["vigente"],
                "modificada_por": found_law.get("modificada_por", []),
                "warning": None if found_law["vigente"] else "Esta ley puede estar derogada",
                "recommendation": "Verificar en SUIN-Juriscol para información actualizada",
            }
        else:
            output = {
                "law_name": law_name,
                "found_in_db": False,
                "vigente": None,
                "warning": "Ley no encontrada en base de referencia. Verificar manualmente.",
                "recommendation": "Consultar SUIN-Juriscol: https://www.suin-juriscol.gov.co/",
            }

        print(
            f"{_GREEN}[TOOL 5] check_law_vigency - Vigente: {output.get('vigente', 'Desconocido')}{_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 5] check_law_vigency - ERROR: {e!s}{_RESET}")
        return {"law_name": law_name, "found_in_db": False, "error": str(e)}



@tool
def find_related_jurisprudence(legal_topic: str, max_results: int = 5) -> dict:
    """
    Busca sentencias y jurisprudencia relacionada a un tema legal.

    Realiza búsqueda semántica filtrando por documentos que contengan
    términos típicos de jurisprudencia (sentencia, corte, tutela, etc.)

    Args:
        legal_topic: Tema legal a buscar jurisprudencia
        max_results: Máximo de sentencias a retornar

    Returns:
        Dictionary con sentencias relacionadas

    Casos de uso:
        - "Jurisprudencia sobre estabilidad laboral reforzada"
        - "Sentencias de la Corte sobre despido sin justa causa"
        - "Tutelas sobre acoso laboral"
    """
    print(f"{_GREEN}[TOOL 6] find_related_jurisprudence - Tema: {legal_topic}{_RESET}")

    try:
        # Búsqueda semántica con términos de jurisprudencia
        search_query = f"sentencia corte jurisprudencia {legal_topic}"
        results = _vectorstore.similarity_search(search_query, k=15)

        # Filtrar documentos que parezcan ser jurisprudencia
        jurisprudence_keywords = [
            "sentencia",
            "corte",
            "tutela",
            "c-",
            "t-",
            "su-",
            "magistrado",
            "demandante",
            "demandado",
            "fallo",
        ]

        jurisprudence_results = []
        for doc in results:
            content_lower = doc.page_content.lower()
            doc_id_lower = doc.metadata.get("doc_id", "").lower()

            # Verificar si contiene términos de jurisprudencia
            if any(kw in content_lower or kw in doc_id_lower for kw in jurisprudence_keywords):
                jurisprudence_results.append(
                    {
                        "content": doc.page_content[:400] + "...",
                        "source": doc.metadata.get("doc_id", "Unknown"),
                        "page": doc.metadata.get("page"),
                        "likely_type": "Sentencia/Jurisprudencia",
                    }
                )
                if len(jurisprudence_results) >= max_results:
                    break

        # Si no hay jurisprudencia específica, indicarlo
        if not jurisprudence_results:
            # Retornar resultados generales como alternativa
            jurisprudence_results = [
                {
                    "content": doc.page_content[:400] + "...",
                    "source": doc.metadata.get("doc_id", "Unknown"),
                    "page": doc.metadata.get("page"),
                    "likely_type": "Normatividad general (no jurisprudencia específica)",
                }
                for doc in results[:max_results]
            ]

        output = {
            "topic": legal_topic,
            "total_found": len(jurisprudence_results),
            "jurisprudence": jurisprudence_results,
            "note": "Resultados basados en búsqueda semántica del corpus disponible",
        }

        print(
            f"{_GREEN}[TOOL 6] find_related_jurisprudence - Encontradas: {len(jurisprudence_results)}{_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 6] find_related_jurisprudence - ERROR: {e!s}{_RESET}")
        return {"topic": legal_topic, "total_found": 0, "jurisprudence": [], "error": str(e)}

@tool
def verify_citation_exists(law_name: str, article_number: str) -> dict:
    """
    Verifica que una citación legal (Ley X, Artículo Y) existe en el corpus.

    Herramienta anti-alucinación: confirma que las referencias legales
    citadas por el LLM realmente existen en la base de conocimiento.

    Args:
        law_name: Nombre de la ley citada
        article_number: Número de artículo citado

    Returns:
        Dictionary indicando si la citación es válida

    Casos de uso:
        - Validar que "Artículo 64 del CST" existe
        - Verificar citaciones en respuestas generadas
        - Control de calidad para evitar hallucinations
    """
    print(f"{_GREEN}[TOOL 7] verify_citation_exists - {law_name}, Art. {article_number}{_RESET}")

    try:
        # Construir query específica
        search_query = f"ARTÍCULO {article_number} {law_name}"
        results = _vectorstore.similarity_search(search_query, k=5)

        # Verificar coincidencia del artículo
        article_pattern = rf"ART[ÍI]CULO\s*{article_number}[.\s\-\:]"

        verified = False
        matching_content = None
        source_doc = None

        for doc in results:
            if re.search(article_pattern, doc.page_content, re.IGNORECASE):
                verified = True
                matching_content = doc.page_content[:300] + "..."
                source_doc = doc.metadata.get("doc_id", "Unknown")
                break

        output = {
            "law_name": law_name,
            "article_number": article_number,
            "citation_verified": verified,
            "source_document": source_doc,
            "matching_excerpt": matching_content,
            "confidence": "high" if verified else "not_found",
            "recommendation": None
            if verified
            else "La citación no se encontró. Verificar manualmente.",
        }

        status = "VERIFICADA" if verified else "NO ENCONTRADA"
        print(f"{_GREEN}[TOOL 7] verify_citation_exists - {status}{_RESET}")
        return output

    except Exception as e:
        print(f"{_RED}[TOOL 7] verify_citation_exists - ERROR: {e!s}{_RESET}")
        return {
            "law_name": law_name,
            "article_number": article_number,
            "citation_verified": False,
            "error": str(e),
        }


@tool
def evaluar_riesgo_laboral(clausula_o_situacion: str) -> str:
    """
    Útil para evaluar el riesgo legal de una situación laboral, un despido o una cláusula de contrato.
    Analiza la situación y devuelve un semáforo de riesgo para el trabajador.
    """
    # Como herramienta, le damos al LLM una estructura estricta que debe llenar.
    plantilla_semaforo = (
        "INSTRUCCIÓN PARA EL ASISTENTE: Acabas de activar la herramienta de evaluación de riesgo. "
        "REGLA DE ORO: PRIMERO debes darle al usuario una respuesta legal completa, empática y detallada "
        "explicando su situación según la ley. LUEGO, al final de tu respuesta, añade EXACTAMENTE esta sección "
        "para resumir visualmente su caso:\n\n"
        "🚦 **SEMÁFORO DE RIESGO LEGAL** 🚦\n"
        "🔴 **ALTO RIESGO / ILEGALIDAD:** (Derechos vulnerados).\n"
        "🟡 **ZONA GRIS:** (Falta de pruebas o prácticas dudosas).\n"
        "🟢 **SEGURO / LEGAL:** (Lo que está en regla).\n\n"
        "💡 **RECOMENDACIÓN:** (Qué debe hacer a continuación. AQUÍ ES DONDE LE SUGIERES REDACTAR UN DOCUMENTO SI ES NECESARIO)."
    )
    return plantilla_semaforo



@tool
def generar_documento_legal(tipo_documento: str, nombre_usuario: str, hechos_clave: str) -> str:
    """
    Útil para redactar borradores legales como 'Derecho de Petición', 'Carta de Renuncia Motivada' o 'Queja Laboral'.

    REGLA DE ORO: Si detectas que al usuario le están vulnerando un derecho, SUGIERE usar esta herramienta primero.

    REGLAS ESTRICTAS PARA USAR ESTA HERRAMIENTA:
    1. NO PUEDES inventar el 'nombre_usuario' ni el 'nombre_empresa_o_jefe'.
    2. NO PUEDES usar corchetes como [Nombre del trabajador].
    3. Si NO TIENES los nombres exactos provistos por el usuario en esta conversación,
       TIENES PROHIBIDO ejecutar esta herramienta. Debes responderle al usuario
       pidiéndole exactamente los datos que te faltan.

    Solo ejecútala si el usuario te dice expresamente 'Sí, genéralo', 'Redacta el documento' o similares.
    """
    fecha_hoy = datetime.now().strftime("%d de %B de %Y")

    borrador = f"""
    📄 **BORRADOR GENERADO AUTOMÁTICAMENTE: {tipo_documento.upper()}** 📄
    
    **Fecha:** {fecha_hoy}
    **De:** {nombre_usuario if nombre_usuario else '[TU NOMBRE AQUÍ]'}
    **Para:** [NOMBRE DEL EMPLEADOR / EMPRESA]
    
    **Asunto:** {tipo_documento}
    
    Respetados señores,
    
    Por medio del presente documento, me dirijo a ustedes para exponer los siguientes hechos:
    {hechos_clave}
    
    Por lo anterior, y amparado en la legislación laboral colombiana y el Código Sustantivo del Trabajo, solicito formalmente:
    [ESCRIBE AQUÍ TU PETICIÓN ESPECÍFICA (Ej: El pago de la liquidación adeudada, el reintegro, etc.)]
    
    Quedo atento(a) a una pronta respuesta conforme a los términos de ley.
    
    Atentamente,
    
    ___________________________
    Firma
    C.C. [TU CÉDULA]
    """
    return borrador


@tool
def query_knowledge_graph(question: str) -> dict:
    """
    Consulta el Knowledge Graph (ontología laboral en GraphDB) mediante SPARQL.

    Esta herramienta accede a la base de conocimiento estructurada que contiene
    información sobre empleados, contratos, salarios, empresas, jornadas laborales,
    beneficios y relaciones entre entidades del dominio laboral colombiano.

    A diferencia de la búsqueda vectorial (semántica sobre texto), esta herramienta
    permite consultas ESTRUCTURADAS sobre relaciones, datos numéricos exactos y
    propiedades específicas de las entidades.

    Args:
        question: Pregunta en lenguaje natural sobre datos estructurados del knowledge graph.
                  Ejemplos:
                  - "¿Cuáles son los empleados de la Empresa Alfa?"
                  - "¿Qué tipo de contrato tiene Ana López?"
                  - "¿Cuánto gana el Coordinador de TI?"
                  - "¿Qué beneficios ofrece la Empresa Beta?"
                  - "Lista todos los contratos de prestación de servicios activos"
                  - "¿En qué departamento trabaja Bruno Díaz?"

    Returns:
        Dictionary con la consulta SPARQL ejecutada, los resultados y el contexto formateado.
    """
    print(f"{_BLUE}[TOOL KG] query_knowledge_graph - Pregunta: {question}{_RESET}")

    try:
        if not settings.GRAPHDB_ENABLED:
            print(f"{_YELLOW}[TOOL KG] GraphDB deshabilitado{_RESET}")
            return {
                "question": question,
                "sparql_query": None,
                "total_results": 0,
                "results": [],
                "context": "",
                "source": "graphdb_disabled",
            }

        from app.rag.graph_retriever import query_graph

        # Lazy import of the LLM to avoid circular imports at module load time.
        # The agents module already initialises gemini_LLM at import; we reuse it.
        from app.rag.llm import get_llm

        llm = get_llm()

        graph_result = query_graph(question, llm)

        output = {
            "question": question,
            "sparql_query": graph_result.get("sparql_query"),
            "total_results": len(graph_result.get("results", [])),
            "results": graph_result.get("results", [])[:10],  # Cap to avoid huge payloads
            "context": graph_result.get("context", ""),
            "source": graph_result.get("source", "graphdb"),
        }

        print(
            f"{_BLUE}[TOOL KG] query_knowledge_graph - Resultados: {output['total_results']}{_RESET}"
        )
        return output

    except Exception as e:
        print(f"{_RED}[TOOL KG] query_knowledge_graph - ERROR: {e!s}{_RESET}")
        return {
            "question": question,
            "sparql_query": None,
            "total_results": 0,
            "results": [],
            "context": "",
            "error": str(e),
        }


TOOLS_LIST = [
    search_by_law_number,
    get_article_text,
    list_laws_by_topic,
    get_document_metadata,
    check_law_vigency,
    find_related_jurisprudence,
    verify_citation_exists,
    evaluar_riesgo_laboral,
    generar_documento_legal,
    query_knowledge_graph,
]

TOOLS_DICT = {
    "search_by_law_number": search_by_law_number,
    "get_article_text": get_article_text,
    "list_laws_by_topic": list_laws_by_topic,
    "get_document_metadata": get_document_metadata,
    "check_law_vigency": check_law_vigency,
    "find_related_jurisprudence": find_related_jurisprudence,
    "verify_citation_exists": verify_citation_exists,
    "evaluar_riesgo_laboral": evaluar_riesgo_laboral,
    "generar_documento_legal": generar_documento_legal,
    "query_knowledge_graph": query_knowledge_graph,
}
