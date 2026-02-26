from __future__ import annotations

import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.api.schemas import ChatResponse, Trace
from app.core.config import settings
from app.rag.prompts import CLASSIFIER_PROMPT, GENERAL_SYSTEM_PROMPT
from app.rag.retriever import recuperar_contexto_dinamico, formatear_documentos_para_gemini
from app.api.schemas import Citation

if TYPE_CHECKING:
    from app.core.config import Settings

_RED = "\033[91m"
_RESET = "\033[0m"

# Ruta absoluta al directorio del proyecto (rag/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_CHROMA_PATH = os.path.join(_PROJECT_ROOT, "db_chroma")

groq_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ groq_LLM ready:", groq_LLM.model_name)

# Conexión Global a tu Base Vectorial
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vectorstore = Chroma(persist_directory=_DB_CHROMA_PATH, embedding_function=embeddings)

# Instanciamos a Gemini para Clasificación y Generación Final
gemini_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Modelo actualizado (gemini-1.5-flash fue deprecado)
    temperature=0.1, #Al bajar un poco la temperatura la respuesta sera mas "natural", sin embargo se puede setear en 0 si queremos respuestas mas "tecnicas" y ceñidas al contexto
    google_api_key=settings.GOOGLE_API_KEY
    )
print("✅ gemini_LLM ready:", gemini_LLM.model)


class ClassifierOutput(BaseModel):
    question: str = Field(description="The original user question.")
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    instruccion_especifica: str # Aquí se guardará la instrucción específica generada por el nodo de intención (e.g. "compara los conceptos A y B", "resume el concepto X", etc.)
    contexto_legal: str # Aqui se guardará el contexto recuperado de la base de datos vectorial
    is_valid: bool
    documentos_recuperados: list # Aquí se guardará la lista de documentos recuperados por el nodo RAG para su uso en las citaciones.

    #rag_prompt: str  # TODO: investigate a better way to connect the nodes, maybe RAG should be a tool that searches the corpus and returns the relevant information to the intent nodes, instead of passing the prompt through the state


#classifier_chain = CLASSIFIER_PROMPT | groq_LLM.with_structured_output(ClassifierOutput)

#Usamos gemini para la clasificación de intención porque es más fuerte en tareas de comprensión y clasificación, mientras que groq lo dejamos para manejo de la lógica del grafo.
classifier_chain = CLASSIFIER_PROMPT | gemini_LLM.with_structured_output(ClassifierOutput)


def classifier_node(state: GraphState):
    question = state["messages"][-1].content
    classification_result = classifier_chain.invoke({"question": question})
    return {"question": classification_result.question, "intent": classification_result.intent}


def general_search_node(state: GraphState):
    messages_for_llm = [GENERAL_SYSTEM_PROMPT] + state["messages"]
    res = groq_LLM.invoke(messages_for_llm)
    print("GENERAL SEARCH RESULT:", res)
    return {"messages": [res]}


def domain_search_node(state: GraphState):
    print(f"{_RED}[DEBUG]: domain_search_node{_RESET}")
    question = state["question"]

    instruccion = (
        #f"Perform a similarity search in the legal document corpus "
        #f"for the following concept or question: '{question}'. "
        #f"Using the retrieved fragments, answer precisely as an expert "
        #f"in Colombian labor law."
        #"IMPORTANT: Your final response MUST be written entirely in Spanish."
        "Act as an expert in Colombian labor law. Read the retrieved legal context, "
        "and answer the user's question directly, precisely, and grounded strictly in the provided law.\n\n"
        f"The user's question is: '{question}'.\n\n"
        "Make sure to cite the relevant articles, laws, or decrees using the provided metadata.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"instruccion_especifica": instruccion}


def summarize_node(state: GraphState):
    print(f"{_RED}[DEBUG]: summarize_node{_RESET}")
    question = state["question"]

    instruccion = (
        #f"Perform a similarity search in the legal document corpus "
        #f"related to: '{question}'. "
        #f"Using the retrieved fragments, generate a clear and structured summary "
        #f"of the legal content found."
        #"IMPORTANT: Your final response MUST be written entirely in Spanish."
        "Act as a legal analyst. Using the retrieved legal context, generate a clear, "
        "structured, and easy-to-understand summary of the consulted topic. "
        "Use bullet points if necessary for better readability.\n\n"
        f"The user's consulted topic is: '{question}'.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"instruccion_especifica": instruccion}


def compare_node(state: GraphState):
    question = state["question"]
    print(f"{_RED}[DEBUG]: compare_node{_RESET}")

    instruccion = (
        #f"Perform a similarity search in the legal document corpus "
        #f"to retrieve information about the legal concepts present in: '{question}'. "
        #f"Using the retrieved fragments, compare those concepts in a structured way, "
        #f"organizing the response into: Definition, Key differences, and Legal implications."
        #"IMPORTANT: Your final response MUST be written entirely in Spanish."
        "Act as an expert in Colombian labor law. Based on the retrieved context, "
        "compare the legal concepts requested by the user in a structured way. "
        "Organize your response strictly into these three sections:\n"
        "1. Definición de los conceptos (Definition of the concepts)\n"
        "2. Diferencias clave (Key differences)\n"
        "3. Implicaciones legales (Legal implications for the employee/employer)\n\n"
        f"The infortmation to compare is: '{question}'.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"instruccion_especifica": instruccion}


def rag_node(state: GraphState):
    #print(f"{_RED}[DEBUG]: rag_node — intent={state['intent']}{_RESET}")
    #rag_prompt = state.get("rag_prompt", "")
    
    #if rag_prompt:
    #    # Use the prompt built by the upstream intent node (domain/summarize/compare)
    #    print(f"{_RED}[DEBUG]: rag_node using rag_prompt: {rag_prompt}{_RESET}")
    #    full_prompt = (
    #        rag_prompt + "\n\nIMPORTANT: Your response must be written entirely in Spanish."
    #    )
    #    res = groq_LLM.invoke(full_prompt)
    #else:
    #    # Fallback: use raw conversation messages (e.g. when coming from validate_route retry)
    #    res = groq_LLM.invoke(state["messages"])
    
    #return {"messages": [res]}
    
    print(f"{_RED}[DEBUG]: rag_node - Ejecutando busqueda vectorial... {_RESET}")
    question = state["question"]
    instruction = state.get("instruccion_especifica", "Answer in spanish the question based on the law.")
    
    #1. El retriever usa Groq internamente para decidir dinámicamente el K de la búsqueda vectorial y buscar en ChromaDB
    documentos = recuperar_contexto_dinamico(question, vectorstore)
    
    #2. Formateamos el resultado para que Gemini lo entienda mejor
    contexto = formatear_documentos_para_gemini(documentos)

    #3. Armamos el prompt para Gemini (Generador final)
    prompt_final = (
        f"You are a legal expert specialized in Colombian labor law.\n\n"
        f"SYSTEM INSTRUCTION: {instruction}\n\n"
        f"USER QUESTION: {question}\n"
        f"RETRIEVED LEGAL CONTEXT (In Spanish): {contexto}\n\n"
        f"REMINDER: Base your answer STRICTLY on the retrieved context above. "
        f"Include citations. Output the final response entirely in SPANISH."
    )
    
    # 4. Gemini redacta la respuesta final
    print(f"{_RED}[DEBUG]: Gemini está redactando la respuesta...{_RESET}")
    res = gemini_LLM.invoke(prompt_final)
    
    #5. Extraemos los documentos recuperados y los convertimos al esquema Citation de FastAPI para incluirlos en la respuesta
    citations_list = []
    for doc in documentos:
        cita = Citation(
            source=doc.metadata.get("doc_id", "Desconocido"),
            page=doc.metadata.get("page", None),
            chunk_id=doc.metadata.get("chunk_id", "N/A"),
            snippet=doc.page_content[:250] + "..." # Un pequeño extracto para el frontend
        )
        citations_list.append(cita)

    
    return {"messages": [res], "contexto_legal": contexto, "documentos_recuperados": citations_list}



def validate_node(state: GraphState):
    answer = state["messages"][-1].content
    print(f"{_RED}[DEBUG]: validate_node{_RESET}")
    # TODO: implement the actual validation logic.
    is_valid = "No sé" not in answer

    return {"is_valid": is_valid}


def validate_route(state: GraphState) -> Literal["rag_node", "__end__"]:
    if state["is_valid"]:
        print(f"{_RED}[DEBUG]: validate_node — answer is valid{_RESET}")
        return END  # Ir directamente al final, saltando el nodo de integración

    print(f"{_RED}[DEBUG]: validate_node — answer is NOT valid, will retry with RAG node{_RESET}")
    return "rag_node"

#Se comenta el nodo de integración porque en esta arquitectura el nodo RAG ya devuelve la respuesta final redactada por Gemini, por lo que no es necesario un nodo adicional para integrar la información. Además, al pasar los documentos recuperados y el contexto legal directamente en el estado, el nodo de validación puede usarlos para tomar decisiones más informadas sobre la validez de la respuesta.
#def integrate_node(state: GraphState):
#    answer = state["messages"][-1].content
#    print(f"{_RED}[DEBUG]: integrate_node{_RESET}")
#    return {
#        "answer": answer,
#        "question": state["question"],
#        "intent": state["intent"],
#        "citations": [],
#    }


def classify_route(
    state: GraphState,
) -> Literal["domain_search_node", "summarize_node", "compare_node", "general_search_node"]:
    intent = state["intent"]
    if intent == "domainSearch":
        return "domain_search_node"
    elif intent == "summarize":
        return "summarize_node"
    elif intent == "compare":
        return "compare_node"
    else:
        return "general_search_node"


graph = StateGraph(GraphState)

graph.add_node("classifier_node", classifier_node)
graph.add_node("domain_search_node", domain_search_node)
graph.add_node("summarize_node", summarize_node)
graph.add_node("compare_node", compare_node)
graph.add_node("general_search_node", general_search_node)
graph.add_node("validate_node", validate_node)
#graph.add_node("integrate_node", integrate_node)
graph.add_node("rag_node", rag_node)

graph.add_edge(START, "classifier_node")
graph.add_conditional_edges("classifier_node", classify_route)

graph.add_edge("domain_search_node", "rag_node")
graph.add_edge("summarize_node", "rag_node")
graph.add_edge("compare_node", "rag_node")
graph.add_edge("general_search_node", "validate_node")

graph.add_edge("rag_node", "validate_node")

graph.add_conditional_edges("validate_node", validate_route)

#graph.add_edge("integrate_node", END)


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
    config = {"configurable": {"thread_id": conversation_id}}
    # Inyectamos la pregunta en el estado inicial
    initial_messages = {"messages": [HumanMessage(content=question)], "question": question}
    #Ejecutamos el grafo y capturamos TODO el estado final
    state_output = chat.invoke(initial_messages, config=config)
    # Extraemos la respuesta del LLM
    response = state_output["messages"][-1].content
    # Extraemos el intent real que calculó el clasificador
    intent_real = state_output.get("intent", "generalSearch")
    # Extraemos los documentos y los convertimos al esquema Citation de FastAPI
    documentos_recuperados = state_output.get("documentos", [])

    #Obtenemos la lista de documentos recuperados por el nodo RAG para incluirlos en las citaciones
    citations_list = state_output.get("documentos_recuperados", [])
    request_id = "test"
    
    #messages = chat.invoke(initial_messages, config=config)["messages"]
    #answer_text = response
    #citations = []
    #intent = ""
    #top_k = 4

    return ChatResponse(
        ok=True,
        request_id=request_id, #TODO generar un id unico como: "req-"+conversation_id, 
        answer=response,
        citations=citations_list,
        trace=Trace(
            intent=intent_real,
            top_k=len(citations_list),
            vector_db=settings.VECTOR_DB,
            llm_provider=settings.LLM_PROVIDER,
        ),
    )
