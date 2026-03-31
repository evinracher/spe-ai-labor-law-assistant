"""
ReAct-based Agents for SPE AI Labor Law Assistant
==================================================

This module implements a multi-node RAG system where each specialized node
uses the ReAct pattern via create_agent: the LLM DECIDES which tools to use
based on the question, rather than using hardcoded regex patterns.

Architecture:
- classifier_node: Deterministic (no tools)
- domain_search_node: ReAct with search tools (list_laws, search_law, get_article, jurisprudence)
- summarize_node: ReAct with content tools (list_laws, get_article, metadata)
- compare_node: ReAct with comparison tools (list_laws, search_law, get_article)
- rag_node: Final generation with retrieved context
- validate_node: ReAct for citation verification (verify_citation, check_vigency)
- general_search_node: No RAG (Groq direct)

Principle: Least Privilege - each node only has access to the tools it needs.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.api.schemas import ChatResponse, Citation, QueryTransformTrace, Trace
from app.core.config import settings
from app.rag.prompts import (
    CLASSIFIER_PROMPT,
    COMPARE_PROMPT,
    DOMAIN_SEARCH_PROMPT,
    DRAFT_DOCUMENT_PROMPT,
    GENERAL_SYSTEM_PROMPT,
    SUMMARIZE_PROMPT,
    VALIDATE_PROMPT,
)
from app.rag.query_transformer import QueryTransformer
from app.rag.retriever import formatear_documentos_para_gemini, recuperar_contexto_dinamico
from app.rag.tools import (
    # Tools registry
    check_law_vigency,
    evaluar_riesgo_laboral,
    find_related_jurisprudence,
    # Tool de generación de documentos legales
    generar_documento_legal,
    get_article_text,
    get_document_metadata,
    list_laws_by_topic,
    # Data Access Tools
    search_by_law_number,
    # Validation Tools
    verify_citation_exists,
)

#

if TYPE_CHECKING:
    from app.core.config import Settings

_RED = "\033[91m"
_RESET = "\033[0m"


def _build_conversation_history(messages: Sequence[BaseMessage], max_turns: int = 5) -> str:
    """Construye un resumen del historial de conversación para pasar a los agentes."""
    if len(messages) <= 1:
        return ""

    # Tomar los últimos N turnos (excluyendo el mensaje actual)
    history_messages = list(messages)[:-1][
        -max_turns * 2 :
    ]  # *2 porque cada turno tiene user+assistant

    if not history_messages:
        return ""

    history_lines = []
    for msg in history_messages:
        role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        # Truncar mensajes largos
        if len(content) > 300:
            content = content[:300] + "..."
        history_lines.append(f"{role}: {content}")

    return "HISTORIAL DE CONVERSACIÓN:\n" + "\n".join(history_lines) + "\n\n"


# Ruta absoluta al directorio del proyecto (rag/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Resolve CHROMA_DIR relative to the project root when it is not absolute
_chroma_dir = settings.CHROMA_DIR
if not _chroma_dir.is_absolute():
    _chroma_dir = (Path(_PROJECT_ROOT) / _chroma_dir).resolve()
_DB_CHROMA_PATH = str(_chroma_dir)

groq_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ groq_LLM ready:", groq_LLM.model_name)

# Conexión Global a tu Base Vectorial - Google embedding-001
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="RETRIEVAL_DOCUMENT",
    google_api_key=settings.GOOGLE_API_KEY,
)
vectorstore = Chroma(persist_directory=_DB_CHROMA_PATH, embedding_function=embeddings)

# Instanciamos a Gemini para Clasificación y Generación Final
gemini_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Modelo actualizado
    temperature=0.1,  # Al bajar un poco la temperatura la respuesta sera mas "natural", sin embargo se puede setear en 0 si queremos respuestas mas "tecnicas" y ceñidas al contexto
    google_api_key=settings.GOOGLE_API_KEY,
)
print("✅ gemini_LLM ready:", gemini_LLM.model)

# Instanciamos el transformador adaptativo de consultas
_query_transformer = QueryTransformer(fast_llm=groq_LLM, strong_llm=gemini_LLM)
print("✅ QueryTransformer ready")

# ====================================================================
# Tool Sets per Node (Principle: Least Privilege)
# ====================================================================

DOMAIN_SEARCH_TOOLS = [
    list_laws_by_topic,
    search_by_law_number,
    get_article_text,
    find_related_jurisprudence,
    evaluar_riesgo_laboral,
]

SUMMARIZE_TOOLS = [
    list_laws_by_topic,
    get_article_text,
    get_document_metadata,
]

COMPARE_TOOLS = [
    list_laws_by_topic,
    search_by_law_number,
    get_article_text,
]

VALIDATE_TOOLS = [
    verify_citation_exists,
    check_law_vigency,
]

DRAFT_DOCUMENT_TOOLS = [
    generar_documento_legal,
]


# ====================================================================
# ReAct Agents per Node (using create_agent)
# ====================================================================

# Agente para búsqueda en dominio legal
domain_search_agent = create_agent(
    model=gemini_LLM,
    tools=DOMAIN_SEARCH_TOOLS,
    system_prompt=DOMAIN_SEARCH_PROMPT,
    name="domain_search_agent",
)

# Agente para resúmenes
summarize_agent = create_agent(
    model=gemini_LLM, tools=SUMMARIZE_TOOLS, system_prompt=SUMMARIZE_PROMPT, name="summarize_agent"
)

# Agente para comparaciones
compare_agent = create_agent(
    model=gemini_LLM, tools=COMPARE_TOOLS, system_prompt=COMPARE_PROMPT, name="compare_agent"
)

# Agente para validación
validate_agent = create_agent(
    model=gemini_LLM, tools=VALIDATE_TOOLS, system_prompt=VALIDATE_PROMPT, name="validate_agent"
)

# Agente redactor de documentos legales
draft_document_agent = create_agent(
    model=gemini_LLM,
    tools=DRAFT_DOCUMENT_TOOLS,
    system_prompt=DRAFT_DOCUMENT_PROMPT,
    name="draft_document_agent",
)


print("✅ ReAct agents created: domain_search, summarize, compare, validate, draft_document")


class ClassifierOutput(BaseModel):
    question: str = Field(description="The original user question.")
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch", "draftDocument"] = (
        Field(description="User intent.")
    )


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch", "draftDocument"]
    instruccion_especifica: str  # Instrucción específica del nodo de intención
    contexto_legal: str  # Contexto recuperado de la base vectorial
    laws_hint: str  # Leyes detectadas por list_laws_by_topic (opcional)
    is_valid: bool
    documentos_recuperados: list  # Documentos para citaciones
    query_transform: dict  # QueryTransformResult serialized for traceability


# Usamos gemini para la clasificación de intención porque es más fuerte en tareas de comprensión y clasificación, mientras que groq lo dejamos para manejo de la lógica del grafo.
classifier_chain = CLASSIFIER_PROMPT | gemini_LLM.with_structured_output(ClassifierOutput)


def classifier_node(state: GraphState):
    question = state["messages"][-1].content

    # Si la conversación tiene al menos 2 mensajes (pregunta y respuesta previa)
    if len(state["messages"]) >= 2:
        last_msg = state["messages"][-2]

        # 1. Extraer el texto de forma segura (por si Gemini devuelve una lista)
        content_raw = last_msg.content
        if isinstance(content_raw, list):
            contenido_anterior = " ".join(str(b) for b in content_raw).lower()
        else:
            contenido_anterior = str(content_raw).lower()

        # 2. Búsqueda de contexto amplia
        bot_pedia_datos = any(p in contenido_anterior for p in ["nombre", "empresa", "empleador"])
        bot_hablaba_documento = any(
            p in contenido_anterior for p in ["documento", "redactar", "carta", "información"]
        )

        if bot_pedia_datos and bot_hablaba_documento:
            print(
                f"{_RED}[DEBUG]: OVERRIDE ACTIVADO - El usuario está dando los datos para el documento.{_RESET}"
            )
            return {"question": question, "intent": "draftDocument"}

    historial = _build_conversation_history(state["messages"], max_turns=10)

    classification_result = classifier_chain.invoke({"question": question, "historial": historial})
    return {"question": classification_result.question, "intent": classification_result.intent}


def general_search_node(state: GraphState):
    """
    Respuestas generales usando Groq.
    """
    messages_for_llm = [GENERAL_SYSTEM_PROMPT] + state["messages"]
    res = groq_LLM.invoke(messages_for_llm)
    print(f"{_RED}[DEBUG]: general_search_node (Groq) - Response ready{_RESET}")
    return {"messages": [res]}


def domain_search_node(state: GraphState):
    """
    Nodo ReAct para búsqueda de información específica en el dominio legal.
    """
    print(f"{_RED}[DEBUG]: domain_search_node (ReAct con contexto){_RESET}")
    question = state["question"]
    contexto_previo = state.get("contexto_legal", "")
    historial = _build_conversation_history(state["messages"])

    # Prompt que incluye el contexto vectorial y el historial
    prompt_con_contexto = (
        f"{historial}"
        f"CONTEXTO LEGAL DISPONIBLE (de la base de datos vectorial):\n"
        f"{contexto_previo}\n\n"
        f"PREGUNTA DEL USUARIO: {question}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. Si el contexto proporcionado es SUFICIENTE para responder, genera la respuesta directamente\n"
        f"2. Si necesitas información MÁS ESPECÍFICA (ley exacta, artículo, jurisprudencia), usa las herramientas\n"
        f"3. Cita las fuentes exactas (Ley X, Artículo Y)\n"
        f"4. Responde SIEMPRE en español\n"
        f"5. Si notas abuso laboral, o riesgos laborales y/o legales, usa la herramienta 'evaluar_riesgo_laboral' e incluye el semáforo al final.\n"
        f"6. NUNCA redactes documentos legales completos aquí. Solo SUGIERE al usuario: 'Si deseas, puedo ayudarte a redactar un documento legal, solo pídeme que lo genere'."
    )

    # Invocar el agente ReAct - él decide si usa tools o responde directo
    result = domain_search_agent.invoke(
        {"messages": [{"role": "user", "content": prompt_con_contexto}]}
    )

    # Extraer la respuesta final
    final_message = result["messages"][-1]
    agent_response = (
        final_message.content if hasattr(final_message, "content") else str(final_message)
    )

    # Log de tools usadas
    tool_calls = [
        msg for msg in result["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls
    ]
    if tool_calls:
        print(
            f"{_RED}[DEBUG]: domain_search_node - Tools adicionales: {len(tool_calls)} llamadas{_RESET}"
        )
    else:
        print(f"{_RED}[DEBUG]: domain_search_node - Contexto suficiente (sin tools){_RESET}")

    return {"messages": [AIMessage(content=agent_response)]}


def summarize_node(state: GraphState):
    """
    Nodo ReAct para generar resúmenes de temas legales.
    """
    print(f"{_RED}[DEBUG]: summarize_node (ReAct con contexto){_RESET}")
    question = state["question"]
    contexto_previo = state.get("contexto_legal", "")
    historial = _build_conversation_history(state["messages"])

    prompt_con_contexto = (
        f"{historial}"
        f"CONTEXTO LEGAL DISPONIBLE:\n{contexto_previo}\n\n"
        f"SOLICITUD: {question}\n\n"
        f"Genera un resumen estructurado. Si el contexto es suficiente, úsalo directamente. "
        f"Si necesitas más detalle de artículos específicos, usa las herramientas."
    )

    result = summarize_agent.invoke(
        {"messages": [{"role": "user", "content": prompt_con_contexto}]}
    )

    final_message = result["messages"][-1]
    agent_response = (
        final_message.content if hasattr(final_message, "content") else str(final_message)
    )

    tool_calls = [
        msg for msg in result["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls
    ]
    if tool_calls:
        print(
            f"{_RED}[DEBUG]: summarize_node - Tools adicionales: {len(tool_calls)} llamadas{_RESET}"
        )
    else:
        print(f"{_RED}[DEBUG]: summarize_node - Contexto suficiente (sin tools){_RESET}")

    return {"messages": [AIMessage(content=agent_response)]}


def compare_node(state: GraphState):
    """
    Nodo ReAct para comparar conceptos legales.
    """
    print(f"{_RED}[DEBUG]: compare_node (ReAct con contexto){_RESET}")
    question = state["question"]
    contexto_previo = state.get("contexto_legal", "")
    historial = _build_conversation_history(state["messages"])

    prompt_con_contexto = (
        f"{historial}"
        f"CONTEXTO LEGAL DISPONIBLE:\n{contexto_previo}\n\n"
        f"SOLICITUD DE COMPARACIÓN: {question}\n\n"
        f"Compara los conceptos solicitados. Si el contexto tiene la información, úsalo. "
        f"Si necesitas artículos específicos de cada concepto, usa las herramientas."
    )

    result = compare_agent.invoke({"messages": [{"role": "user", "content": prompt_con_contexto}]})

    final_message = result["messages"][-1]
    agent_response = (
        final_message.content if hasattr(final_message, "content") else str(final_message)
    )

    tool_calls = [
        msg for msg in result["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls
    ]
    if tool_calls:
        print(
            f"{_RED}[DEBUG]: compare_node - Tools adicionales: {len(tool_calls)} llamadas{_RESET}"
        )
    else:
        print(f"{_RED}[DEBUG]: compare_node - Contexto suficiente (sin tools){_RESET}")

    return {"messages": [AIMessage(content=agent_response)]}


def rag_node(state: GraphState):
    """
    Retrieval-only node with adaptive query transformation.

    Applies HyDE, Decomposition, or passes the query through unchanged depending
    on the QueryTransformer's analysis. Retrieved documents are deduplicated across
    all effective queries before being stored in state.
    """
    print(f"{_RED}[DEBUG]: rag_node - Adaptive retrieval started{_RESET}")
    question = state["question"]

    # 1. Transform the query
    transform_result = _query_transformer.transform(question)
    print(
        f"{_RED}[DEBUG]: rag_node - strategy={transform_result.strategy.value}, "
        f"queries={len(transform_result.effective_queries)}{_RESET}"
    )

    # 2. Retrieve for each effective query; deduplicate by chunk_id
    all_docs: list = []
    seen_chunk_ids: set[str] = set()

    for effective_query in transform_result.effective_queries:
        docs = recuperar_contexto_dinamico(effective_query, vectorstore)
        for doc in docs:
            chunk_id: str = doc.metadata.get("chunk_id") or doc.page_content[:60]
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                all_docs.append(doc)

    contexto_vectorial = formatear_documentos_para_gemini(all_docs)
    print(f"{_RED}[DEBUG]: rag_node - Total unique docs: {len(all_docs)}{_RESET}")

    # 3. Build citations
    citations_list = []
    for doc in all_docs:
        cita = Citation(
            source=doc.metadata.get("doc_id", "Desconocido"),
            page=doc.metadata.get("page", None),
            chunk_id=doc.metadata.get("chunk_id", "N/A"),
            snippet=doc.page_content[:250] + "...",
        )
        citations_list.append(cita)

    return {
        "contexto_legal": contexto_vectorial,
        "documentos_recuperados": citations_list,
        "query_transform": transform_result.model_dump(),
    }


def validate_node(state: GraphState):
    """
    Nodo ReAct de validación que decide autónomamente:
    - Qué citaciones verificar con verify_citation_exists
    - Qué leyes revisar con check_law_vigency
    - Si la respuesta es válida o necesita corrección
    """
    answer_content = state["messages"][-1].content
    # Asegurar que answer sea string
    answer = str(answer_content) if not isinstance(answer_content, str) else answer_content
    intent = state.get("intent", "generalSearch")
    print(f"{_RED}[DEBUG]: validate_node (ReAct) - intent={intent}{_RESET}")

    # Validación básica primero (criterios que no necesitan tools)
    has_content = len(answer.strip()) > 50
    uncertainty_phrases = [
        "no sé",
        "no tengo información",
        "no puedo responder",
        "no encontré",
        "fuera de mi conocimiento",
        "no dispongo",
    ]
    not_uncertain = not any(phrase in answer.lower() for phrase in uncertainty_phrases)

    # Para intents legales, usar el agente ReAct para validación profunda
    if intent in ["domainSearch", "summarize", "compare"]:
        # Construir prompt para el agente validador
        validation_request = (
            f"Valida la siguiente respuesta legal:\n\n"
            f"RESPUESTA A VALIDAR:\n{answer}\n\n"
            f"Por favor:\n"
            f"1. Identifica las citaciones legales mencionadas (artículos, leyes, decretos)\n"
            f"2. Verifica si existen las citaciones principales usando verify_citation_exists\n"
            f"3. Verifica si las leyes mencionadas están vigentes usando check_law_vigency\n"
            f"4. Indica si la respuesta es VÁLIDA o NO VÁLIDA y por qué"
        )

        try:
            result = validate_agent.invoke(
                {"messages": [{"role": "user", "content": validation_request}]}
            )

            final_message = result["messages"][-1]
            # validation_result = final_message.content if hasattr(final_message, 'content') else str(final_message)

            if isinstance(final_message.content, list):
                validation_result = " ".join(str(b) for b in final_message.content)
            else:
                validation_result = str(final_message.content)

            # Log de tools usadas
            tool_calls = [
                msg for msg in result["messages"] if hasattr(msg, "tool_calls") and msg.tool_calls
            ]
            if tool_calls:
                print(
                    f"{_RED}[DEBUG]: validate_node - Validaciones ejecutadas: {len(tool_calls)} tools{_RESET}"
                )

            # Determinar validez basado en respuesta del agente
            validation_lower = validation_result.lower()
            is_valid_from_agent = (
                "válida" in validation_lower
                and "no válida" not in validation_lower
                and "inválida" not in validation_lower
            )

            print(
                f"{_RED}[DEBUG]: validate_node - Resultado agente: {'VÁLIDA' if is_valid_from_agent else 'NO VÁLIDA'}{_RESET}"
            )

            # Combinar criterios básicos con validación del agente
            is_valid = has_content and not_uncertain and is_valid_from_agent

        except Exception as e:
            print(f"{_RED}[DEBUG]: validate_node - Error en agente: {e}{_RESET}")
            # Fallback a validación básica
            legal_terms = ["artículo", "ley", "decreto", "código", "art.", "numeral"]
            has_legal_reference = any(term in answer.lower() for term in legal_terms)
            is_valid = has_content and not_uncertain and has_legal_reference
    else:
        # Para generalSearch, validación básica
        is_valid = has_content and not_uncertain

    print(
        f"{_RED}[DEBUG]: validate_node - valid={is_valid} "
        f"(content={has_content}, certain={not_uncertain}){_RESET}"
    )

    return {"is_valid": is_valid}


def draft_document_node(state: GraphState):
    print(f"{_RED}[DEBUG]: draft_document_node (ReAct){_RESET}")
    question = state["question"]
    contexto_previo = state.get("contexto_legal", "")
    historial = _build_conversation_history(state["messages"])

    prompt_con_contexto = (
        f"{historial}"
        f"CONTEXTO LEGAL (Para citar leyes en el documento si es necesario):\n{contexto_previo}\n\n"
        f"SOLICITUD DEL USUARIO: {question}\n\n"
        f"ERES UN ABOGADO REDACTOR. El usuario quiere que generes un documento legal.\n"
        f"REGLAS ESTRICTAS DE REDACCIÓN:\n"
        f"1. ANALIZA LA INFORMACIÓN: Para usar tu herramienta 'generar_documento_legal', necesitas saber a quién va dirigido (nombre de la empresa/jefe) y detalles básicos de los hechos.\n"
        f"2. ACCIÓN SI FALTAN DATOS: NO uses la herramienta y NO redactes nada. Limítate a responderle al usuario amablemente pidiendo los datos exactos que te faltan (Tu nombre completo, el nombre de la empresa o tu jefe, y el motivo exacto de la reclamación).\n"
        f"3. FILTRO DE VIABILIDAD LEGAL: Si al leer los hechos notas que el usuario cometió una falta gravísima (ej: robo, agresión comprobada) o que la solicitud carece de viabilidad legal evidente (ej: despido es COMPLETAMENTE LEGAL bajo el Código Sustantivo del Trabajo), NO redactes el documento de inmediato. Adviértele de forma respetuosa que sus acciones constituyen una 'Justa Causa' de despido y que un proceso legal tendría muy pocas probabilidades de éxito. Pregúntale si, asumiendo este riesgo, aún desea generar el documento.\n"
        f"4. SI TIENES LOS DATOS Y ES VIABLE: Usa la herramienta 'generar_documento_legal'."
        f"5. TIENES ESTRICTAMENTE PROHIBIDO redactar el documento legal tú mismo en el chat. La ÚNICA forma permitida de entregar un documento es invocando tu herramienta 'generar_documento_legal'.\n"
        f"6. PROHIBIDO USAR CORCHETES: Si para generar el documento necesitas usar espacios en blanco o corchetes como [Tu Nombre] o [Nombre de la Empresa], SIGNIFICA QUE TE FALTAN DATOS.\n"
    )

    result = draft_document_agent.invoke(
        {"messages": [{"role": "user", "content": prompt_con_contexto}]}
    )

    final_message = result["messages"][-1]
    agent_response = (
        final_message.content if hasattr(final_message, "content") else str(final_message)
    )

    return {"messages": [AIMessage(content=agent_response)]}


def validate_route(state: GraphState) -> Literal["rag_node", "__end__"]:
    if state["is_valid"]:
        print(f"{_RED}[DEBUG]: validate_node — answer is valid{_RESET}")
        return END  # Ir directamente al final, saltando el nodo de integración

    print(f"{_RED}[DEBUG]: validate_node — answer is NOT valid, will retry with RAG node{_RESET}")
    return "rag_node"


def classify_route(
    state: GraphState,
) -> Literal["rag_node", "general_search_node"]:
    """Ruta después del classifier: RAG para intents legales, directo para general."""
    intent = state["intent"]
    if intent in ["domainSearch", "summarize", "compare", "draftDocument"]:
        return "rag_node"  # Primero retrieval
    else:
        return "general_search_node"  # No necesita RAG


def rag_route(
    state: GraphState,
) -> Literal["domain_search_node", "summarize_node", "compare_node", "draft_document_node"]:
    """Ruta después del rag_node: al nodo experto según intent."""
    intent = state["intent"]
    if intent == "domainSearch":
        return "domain_search_node"
    elif intent == "summarize":
        return "summarize_node"
    elif intent == "compare":
        return "compare_node"
    elif intent == "draftDocument":
        return "draft_document_node"


graph = StateGraph(GraphState)

graph.add_node("classifier_node", classifier_node)
graph.add_node("domain_search_node", domain_search_node)
graph.add_node("summarize_node", summarize_node)
graph.add_node("compare_node", compare_node)
graph.add_node("general_search_node", general_search_node)
graph.add_node("validate_node", validate_node)
graph.add_node("draft_document_node", draft_document_node)
# graph.add_node("integrate_node", integrate_node)
graph.add_node("rag_node", rag_node)

graph.add_edge(START, "classifier_node")
graph.add_conditional_edges("classifier_node", classify_route)

# Flujo Opción C: classifier → rag_node (retrieval) → intent_node (genera) → validate
graph.add_conditional_edges("rag_node", rag_route)  # rag_node → experto según intent
graph.add_edge("domain_search_node", "validate_node")
graph.add_edge("summarize_node", "validate_node")
graph.add_edge("compare_node", "validate_node")
graph.add_edge("draft_document_node", "validate_node")
graph.add_edge("general_search_node", "validate_node")  # No necesita RAG
graph.add_conditional_edges("validate_node", validate_route)

memory = InMemorySaver()
chat = graph.compile(checkpointer=memory)
"""""
# ----------------------------------------
# Generar diagrama Mermaid del grafo
# ----------------------------------------

if __name__ == "__main__":
    mermaid_code = chat.get_graph().draw_mermaid()
    print("\n====== MERMAID GRAPH ======\n")
    print(mermaid_code)
"""


def ask_chat(question: str, settings: Settings, conversation_id: str = "conversation_1"):
    if conversation_id is None:
        conversation_id = "conversation_1"

    config = {"configurable": {"thread_id": conversation_id}}
    # Inyectamos la pregunta en el estado inicial
    initial_messages = {"messages": [HumanMessage(content=question)], "question": question}
    # Ejecutamos el grafo y capturamos TODO el estado final
    state_output = chat.invoke(initial_messages, config=config)
    # Extraemos la respuesta del LLM (puede venir como string o lista de content blocks)
    raw_content = state_output["messages"][-1].content
    if isinstance(raw_content, list):
        # Gemini a veces devuelve lista de bloques: [{'type': 'text', 'text': '...'}]
        response = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )
    else:
        response = raw_content
    # Extraemos el intent real que calculó el clasificador
    intent_real = state_output.get("intent", "generalSearch")
    # Extraemos los documentos y los convertimos al esquema Citation de FastAPI
    # documentos_recuperados = state_output.get("documentos", []) TODO: validate if remove

    # Para generalSearch no devolvemos citaciones (no usa RAG)
    if intent_real == "generalSearch":
        citations_list = []
    else:
        # Obtenemos la lista de documentos recuperados por el nodo RAG para incluirlos en las citaciones
        citations_list = state_output.get("documentos_recuperados", [])
    request_id = f"req-{uuid.uuid4().hex[:8]}-{conversation_id}"

    # Build QueryTransformTrace if available (only present for RAG intents)
    qt_data = state_output.get("query_transform")
    qt_trace = QueryTransformTrace(**qt_data) if qt_data else None

    return ChatResponse(
        ok=True,
        request_id=request_id,
        answer=response,
        citations=citations_list,
        trace=Trace(
            intent=intent_real,
            top_k=len(citations_list),
            vector_db=settings.VECTOR_DB,
            llm_provider=settings.LLM_PROVIDER,
            query_transform=qt_trace,
        ),
    )
