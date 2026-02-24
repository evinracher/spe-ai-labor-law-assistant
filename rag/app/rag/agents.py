from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.api.schemas import ChatResponse, Trace
from app.core.config import settings
from app.rag.prompts import CLASSIFIER_PROMPT, GENERAL_SYSTEM_PROMPT

if TYPE_CHECKING:
    from app.core.config import Settings

classifier_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ classifier_LLM ready:", classifier_LLM.model_name)



class ClassifierOutput(BaseModel):
    question: str = Field(description="The original user question.")
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    is_valid: bool


classifier_chain = CLASSIFIER_PROMPT | classifier_LLM.with_structured_output(ClassifierOutput)


def classifier_node(state: GraphState):
    question = state["messages"][-1].content
    classification_result = classifier_chain.invoke({"question": question})
    return {"question": classification_result.question, "intent": classification_result.intent}


def general_search_node(state: GraphState):
    messages_for_llm = [GENERAL_SYSTEM_PROMPT] + state["messages"]
    res = classifier_LLM.invoke(messages_for_llm)
    print("GENERAL SEARCH RESULT:", res)
    return {"messages": [res]}

def domain_search_node(state: GraphState):
    question = state["question"]

    prompt = f"""
    Eres un experto en derecho laboral colombiano.
    Responde la siguiente pregunta de forma precisa:

    {question}
    """

    response = classifier_LLM.invoke(prompt)

    return {
        "messages": [response]
    }

def summarize_node(state: GraphState):
    question = state["question"]

    prompt = f"""
    Resume el siguiente contenido jurídico de manera clara y estructurada:

    {question}
    """

    response = classifier_LLM.invoke(prompt)

    return {
        "messages": [response]
    }

def compare_node(state: GraphState):
    question = state["question"]

    prompt = f"""
    Compara los siguientes conceptos jurídicos de manera estructurada:

    {question}

    Organiza la respuesta en:
    - Definición
    - Diferencias clave
    - Implicaciones legales
    """

    response = classifier_LLM.invoke(prompt)

    return {
        "messages": [response]
    }


def rag_node(state: GraphState):
    # In a real RAG, you'd do retrieval here based on state["question"] and state["intent"]
    # For demonstration, we'll just have the LLM respond based on current messages.
    messages_for_llm = state["messages"]
    res = classifier_LLM.invoke(messages_for_llm)
    print("RAG REQUEST RESULT:", state["question"], state["intent"])
    return {"messages": [res]}

def validate_node(state: GraphState):
    answer = state["messages"][-1].content

    # lógica básica (luego será con LLM)
    is_valid = "No sé" not in answer

    return {
        "is_valid": is_valid
    }

def validate_route(state: GraphState) -> Literal["rag_node", "integrate_node"]:
    if state["is_valid"]:
        return "integrate_node"
    return "rag_node"

def integrate_node(state: GraphState):
    answer = state["messages"][-1].content

    return {
        "answer": answer,
        "question": state["question"],
        "intent": state["intent"],
        "citations": []
    }


def classify_route(state: GraphState) -> Literal["domain_search_node", "summarize_node", "compare_node", "general_search_node"]:
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
graph.add_node("integrate_node", integrate_node)
graph.add_node("rag_node", rag_node)

graph.add_edge(START, "classifier_node")
graph.add_conditional_edges("classifier_node", classify_route)

graph.add_edge("domain_search_node", "rag_node")
graph.add_edge("summarize_node", "rag_node")
graph.add_edge("compare_node", "rag_node")
graph.add_edge("general_search_node", "validate_node")

graph.add_edge("rag_node", "validate_node")

graph.add_conditional_edges("validate_node", validate_route)

graph.add_edge("integrate_node", END)



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
    initial_messages = {"messages": [HumanMessage(content=question)]}
    messages = chat.invoke(initial_messages, config=config)["messages"]
    response = messages[-1].content
    answer_text = response
    citations = []
    intent = ""
    top_k = 4
    request_id = "test"

    return ChatResponse(
        ok=True,
        request_id=request_id,
        answer=answer_text,
        citations=citations,
        trace=Trace(
            intent=intent,
            top_k=top_k,
            vector_db=settings.VECTOR_DB,
            llm_provider=settings.LLM_PROVIDER,
        ),
    )
