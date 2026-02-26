from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.api.schemas import ChatResponse, Citation, Trace
from app.core.config import settings
from app.rag.prompts import CLASSIFIER_PROMPT, GENERAL_SYSTEM_PROMPT
from app.rag.tools import MAX_CITATIONS, generate_mock_citations

if TYPE_CHECKING:
    from app.core.config import Settings

_RED = "\033[91m"
_RESET = "\033[0m"


grop_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ grop_LLM ready:", grop_LLM.model_name)


class ClassifierOutput(BaseModel):
    question: str = Field(description="The original user question.")
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    rag_prompt: str  # TODO: investigate a better way to connect the nodes, maybe RAG should be a tool that searches the corpus and returns the relevant information to the intent nodes, instead of passing the prompt through the state
    citations: list[Citation]
    is_valid: bool


classifier_chain = CLASSIFIER_PROMPT | grop_LLM.with_structured_output(ClassifierOutput)


def classifier_node(state: GraphState):
    question = state["messages"][-1].content
    classification_result = classifier_chain.invoke({"question": question})
    return {"question": classification_result.question, "intent": classification_result.intent}


def general_search_node(state: GraphState):
    messages_for_llm = [GENERAL_SYSTEM_PROMPT] + state["messages"]
    res = grop_LLM.invoke(messages_for_llm)
    print("GENERAL SEARCH RESULT:", res)
    return {"messages": [res]}


def domain_search_node(state: GraphState):
    print(f"{_RED}[DEBUG]: domain_search_node{_RESET}")
    question = state["question"]

    rag_prompt = (
        f"Perform a similarity search in the legal document corpus "
        f"for the following concept or question: '{question}'. "
        f"Using the retrieved fragments, answer precisely as an expert "
        f"in Colombian labor law."
    )

    return {"rag_prompt": rag_prompt}


def summarize_node(state: GraphState):
    print(f"{_RED}[DEBUG]: summarize_node{_RESET}")
    question = state["question"]

    rag_prompt = (
        f"Perform a similarity search in the legal document corpus "
        f"related to: '{question}'. "
        f"Using the retrieved fragments, generate a clear and structured summary "
        f"of the legal content found."
    )

    return {"rag_prompt": rag_prompt}


def compare_node(state: GraphState):
    question = state["question"]
    print(f"{_RED}[DEBUG]: compare_node{_RESET}")

    rag_prompt = (
        f"Perform a similarity search in the legal document corpus "
        f"to retrieve information about the legal concepts present in: '{question}'. "
        f"Using the retrieved fragments, compare those concepts in a structured way, "
        f"organizing the response into: Definition, Key differences, and Legal implications."
    )

    return {"rag_prompt": rag_prompt}


# TODO: the answer shouldn't include details about the similarity search, corpus or anything technical.
# only give the final answer to the user
# this could be a tool: normalize_answer (removes technical details from the answer and leaves only the final answer to the user)
def rag_node(state: GraphState):
    print(f"{_RED}[DEBUG]: rag_node — intent={state['intent']}{_RESET}")
    rag_prompt = state.get("rag_prompt", "")
    question = state["question"]

    # Generate mock citations via the tool
    raw_citations: list[dict] = generate_mock_citations.invoke(
        {"question": question, "max_citations": MAX_CITATIONS}
    )
    citations = [Citation(**c) for c in raw_citations]
    print(f"{_RED}[DEBUG]: rag_node — generated {len(citations)} citations{_RESET}")

    if rag_prompt:
        # Use the prompt built by the upstream intent node (domain/summarize/compare)
        print(f"{_RED}[DEBUG]: rag_node using rag_prompt: {rag_prompt}{_RESET}")
        full_prompt = (
            rag_prompt + "\n\nIMPORTANT: Your response must be written entirely in Spanish."
        )
        res = grop_LLM.invoke(full_prompt)
    else:
        # Fallback: use raw conversation messages (e.g. when coming from validate_route retry)
        res = grop_LLM.invoke(state["messages"])

    return {"messages": [res], "citations": citations}


def validate_node(state: GraphState):
    answer = state["messages"][-1].content
    print(f"{_RED}[DEBUG]: validate_node{_RESET}")
    # TODO: implement the actual validation logic.
    is_valid = "No sé" not in answer

    return {"is_valid": is_valid}


def validate_route(state: GraphState) -> Literal["rag_node", "integrate_node"]:
    if state["is_valid"]:
        print(f"{_RED}[DEBUG]: validate_node — answer is valid{_RESET}")
        return "integrate_node"

    print(f"{_RED}[DEBUG]: validate_node — answer is NOT valid, will retry with RAG node{_RESET}")
    return "rag_node"


def integrate_node(state: GraphState):
    answer = state["messages"][-1].content
    print(f"{_RED}[DEBUG]: integrate_node{_RESET}")
    return {
        "answer": answer,
        "question": state["question"],
        "intent": state["intent"],
        "citations": state.get("citations", []),
    }


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
    result = chat.invoke(initial_messages, config=config)
    answer_text = result["messages"][-1].content
    citations: list[Citation] = result.get("citations", [])
    intent = result.get("intent", "")
    top_k = MAX_CITATIONS
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
        ),
    )
