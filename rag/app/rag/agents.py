from __future__ import annotations

import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.api.schemas import ChatResponse, Citation, ToolTraceStep, Trace, WorkflowTrace
from app.rag.prompts import GENERAL_SYSTEM_PROMPT
from app.rag.retriever import formatear_documentos_para_gemini

# Import formal Tools (format_citations_in_text is re-exported from tools)
from app.rag.tools import (
    classify_intent,
    format_citations_in_text,
    generate_grounded_answer,
    semantic_search,
    validate_answer,
)

if TYPE_CHECKING:
    from app.core.config import Settings

_RED = "\033[91m"
_RESET = "\033[0m"

# Ruta absoluta al directorio del proyecto (rag/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_CHROMA_PATH = os.path.join(_PROJECT_ROOT, "db_chroma")

# Note: LLM instances are now managed in tools.py to avoid duplication
# They are imported and used through the Tools interface


class ClassifierOutput(BaseModel):
    question: str = Field(description="The original user question.")
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    # Retrieved context from semantic_search tool
    contexto_legal: str
    # Documents with metadata for citations
    documentos_recuperados: list
    # Tool execution traces for debugging
    tool_traces: dict
    # Validation result from validate_answer tool
    validation_result: dict
    # Whether final answer is valid
    is_valid: bool


# Note: classifier_chain is now handled internally by Tool 1 (classify_intent)
# from app/rag/tools.py, which uses Gemini for intent classification


def classifier_node(state: GraphState):
    """
    Node 1: CLASSIFY INTENT (using Tool 1: classify_intent)

    Routes user query to appropriate handler.
    Uses formal Tool: classify_intent()
    """
    from datetime import datetime

    question = state["messages"][-1].content

    # Call Tool 1: classify_intent (use .invoke() for LangChain Tool)
    classification_result = classify_intent.invoke({"question": question})

    tool_trace = {
        "tool_name": "classify_intent",
        "input": {"question": question[:100]},
        "output": classification_result,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "question": classification_result["question"],
        "intent": classification_result["intent"],
        "tool_traces": {**state.get("tool_traces", {}), "classify_intent": tool_trace},
    }


def general_search_node(state: GraphState):
    """
    Node 2: GENERAL SEARCH (No RAG)

    For general queries that don't require legal corpus search.
    Skips semantic_search and generate_grounded_answer tools.
    """
    messages_for_llm = [GENERAL_SYSTEM_PROMPT] + state["messages"]
    from app.rag.tools import gemini_LLM

    res = gemini_LLM.invoke(messages_for_llm)
    print(f"{_RED}[GRAPH] general_search_node - Response ready{_RESET}")
    return {"messages": [res]}


def domain_search_node(state: GraphState):
    """
    Node 3: DOMAIN SEARCH (RAG Path)

    Prepares instruction for legal domain queries.
    Next: semantic_search tool will be called in rag_node.
    """
    print(f"{_RED}[GRAPH] domain_search_node - Preparing RAG workflow{_RESET}")
    question = state["question"]

    instruction = (
        "Act as an expert in Colombian labor law. Read the retrieved legal context, "
        "and answer the user's question directly, precisely, and grounded strictly in the provided law.\n\n"
        f"The user's question is: '{question}'.\n\n"
        "Make sure to cite the relevant articles, laws, or decrees using the provided metadata.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"intent": "domainSearch"}


def summarize_node(state: GraphState):
    """
    Node 4: SUMMARIZE (RAG Path)

    Prepares instruction for summarization tasks.
    Will use semantic_search and generate_grounded_answer tools.
    """
    print(f"{_RED}[GRAPH] summarize_node - Preparing summarization workflow{_RESET}")
    question = state["question"]

    instruction = (
        "Act as a legal analyst. Using the retrieved legal context, generate a clear, "
        "structured, and easy-to-understand summary of the consulted topic. "
        "Use bullet points if necessary for better readability.\n\n"
        f"The user's consulted topic is: '{question}'.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"intent": "summarize"}


def compare_node(state: GraphState):
    """
    Node 5: COMPARE (RAG Path)

    Prepares instruction for legal concept comparison.
    Will use semantic_search and generate_grounded_answer tools.
    """
    print(f"{_RED}[GRAPH] compare_node - Preparing comparison workflow{_RESET}")
    question = state["question"]

    instruction = (
        "Act as an expert in Colombian labor law. Based on the retrieved context, "
        "compare the legal concepts requested by the user in a structured way. "
        "Organize your response strictly into these three sections:\n"
        "1. Definición de los conceptos (Definition of the concepts)\n"
        "2. Diferencias clave (Key differences)\n"
        "3. Implicaciones legales (Legal implications for the employee/employer)\n\n"
        f"The information to compare is: '{question}'.\n\n"
        "IMPORTANT: Your final response MUST be written entirely in Spanish."
    )

    return {"intent": "compare"}


def rag_node(state: GraphState):
    """
    Node 6: RAG ORCHESTRATION (Core Tools 2-4 Execution)

    Orchestrates the RAG pipeline:
    1. Tool 2: semantic_search() - Retrieves documents from Chroma
    2. Tool 4: generate_grounded_answer() - Generates answer with citations

    Workflow:
    - Calls semantic_search to retrieve relevant documents
    - Formats context for Gemini
    - Calls generate_grounded_answer for final response with citations

    Returns:
    - messages: LLM response
    - contexto_legal: Formatted context (for validation)
    - documentos_recuperados: Citations list (for frontend)
    """

    print(f"{_RED}[GRAPH] rag_node - Executing RAG pipeline...{_RESET}")
    question = state["question"]
    intent = state["intent"]

    # ===== TOOL 2: semantic_search =====
    print(f"{_RED}[GRAPH] Calling Tool 2: semantic_search{_RESET}")
    search_result = semantic_search.invoke({"query": question})

    if search_result.get("total_results", 0) == 0:
        print(f"{_RED}[GRAPH] No documents retrieved, fallback to general response{_RESET}")
        from app.rag.tools import gemini_LLM

        res = gemini_LLM.invoke(
            f"Answer this question in Spanish: {question}\n"
            "Note: No relevant legal documents were found in the corpus."
        )
        return {
            "messages": [res],
            "contexto_legal": "No documents found",
            "documentos_recuperados": [],
            "is_valid": True,
            "tool_traces": {
                **state.get("tool_traces", {}),
                "semantic_search": {"result": search_result},
            },
        }

    # Extract documents with metadata
    raw_documents = search_result.get("documents", [])
    contexto = formatear_documentos_para_gemini(
        [
            type("Doc", (), {"page_content": doc["content"], "metadata": doc["metadata"]})()
            for doc in raw_documents
        ]
    )

    # ===== TOOL 4: generate_grounded_answer =====
    print(f"{_RED}[GRAPH] Calling Tool 4: generate_grounded_answer{_RESET}")
    answer_result = generate_grounded_answer.invoke(
        {"question": question, "context": contexto, "intent": intent, "documents": raw_documents}
    )

    from langchain_core.messages import AIMessage

    formatted_answer = format_citations_in_text.invoke({"text": answer_result["answer"]})
    response_message = AIMessage(content=formatted_answer)

    # Build citations
    citations_list = [
        Citation(
            source=cit.get("source", "Unknown"),
            page=cit.get("page"),
            chunk_id=cit.get("chunk_id", "N/A"),
            snippet=cit.get("snippet", ""),
        )
        for cit in answer_result.get("citations", [])
    ]

    tool_traces = state.get("tool_traces", {})
    tool_traces.update(
        {
            "semantic_search": {
                "query": question,
                "results": search_result["total_results"],
                "top_k_used": search_result.get("top_k_used"),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "generate_grounded_answer": {
                "citations": len(citations_list),
                "intent_used": intent,
                "tokens_used": answer_result.get("tokens_used", 0),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            },
        }
    )

    return {
        "messages": [response_message],
        "contexto_legal": contexto,
        "documentos_recuperados": citations_list,
        "tool_traces": tool_traces,
    }


def validate_node(state: GraphState):
    """
    Node 7: VALIDATE ANSWER (Tool 5: validate_answer)

    Quality assessment before returning to user.
    Uses Tool 5: validate_answer() to detect:
    - Coherence issues
    - Hallucinations
    - Grounding problems
    - Completeness

    If validation fails, triggers rag_node retry.
    """
    answer = state["messages"][-1].content
    context = state.get("contexto_legal", "")
    question = state["question"]

    print(f"{_RED}[GRAPH] validate_node - Assessing answer quality (Tool 5)...{_RESET}")

    # ===== TOOL 5: validate_answer =====
    validation_result = validate_answer.invoke(
        {"question": question, "answer": answer, "context": context}
    )

    is_valid = validation_result.get("is_valid", False)

    print(
        f"{_RED}[GRAPH] validate_node - Valid: {is_valid}, "
        f"Hallucination: {validation_result.get('hallucination_detected', False)}{_RESET}"
    )

    tool_traces = state.get("tool_traces", {})
    tool_traces["validate_answer"] = {
        **validation_result,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }

    return {
        "is_valid": is_valid,
        "validation_result": validation_result,
        "tool_traces": tool_traces,
    }


def validate_route(state: GraphState) -> Literal["rag_node", "__end__"]:
    """
    Router: Decision based on validation result.

    If validation passes: Go to END
    If validation fails: Retry RAG node for refinement (max 1 retry)
    """
    if state["is_valid"]:
        print(f"{_RED}[GRAPH] validate_route - Answer is VALID, ending{_RESET}")
        return END

    # Prevent infinite loops: check if already retried
    retry_count = state.get("tool_traces", {}).get("rag_node_retry_count", 0)
    if retry_count >= 1:
        print(f"{_RED}[GRAPH] validate_route - Max retries reached, ending{_RESET}")
        return END

    print(f"{_RED}[GRAPH] validate_route - Invalid answer, retrying RAG node{_RESET}")
    return "rag_node"

def classify_route(
    state: GraphState,
) -> Literal["domain_search_node", "summarize_node", "compare_node", "general_search_node"]:
    """
    Router: Route based on classified intent.

    Intent → Handler mapping:
    - domainSearch → domain_search_node → rag_node (RAG pipeline)
    - summarize → summarize_node → rag_node (RAG pipeline)
    - compare → compare_node → rag_node (RAG pipeline)
    - generalSearch → general_search_node (Direct LLM, no RAG)
    """
    intent = state["intent"]
    print(f"{_RED}[GRAPH] classify_route - Routing intent: {intent}{_RESET}")

    if intent == "domainSearch":
        return "domain_search_node"
    elif intent == "summarize":
        return "summarize_node"
    elif intent == "compare":
        return "compare_node"
    else:
        return "general_search_node"


graph = StateGraph(GraphState)

# Nodes: classifier -> intent routers -> handlers
graph.add_node("classifier_node", classifier_node)
graph.add_node("domain_search_node", domain_search_node)
graph.add_node("summarize_node", summarize_node)
graph.add_node("compare_node", compare_node)
graph.add_node("general_search_node", general_search_node)
graph.add_node("rag_node", rag_node)
graph.add_node("validate_node", validate_node)

# Edges: Main flow
graph.add_edge(START, "classifier_node")
graph.add_conditional_edges("classifier_node", classify_route)

# RAG path: domain/summarize/compare → rag_node → validate
graph.add_edge("domain_search_node", "rag_node")
graph.add_edge("summarize_node", "rag_node")
graph.add_edge("compare_node", "rag_node")

# General path: no RAG validation
graph.add_edge("general_search_node", "validate_node")

# RAG path: rag_node → validate_node
graph.add_edge("rag_node", "validate_node")

# Validation: decide whether to retry or end
graph.add_conditional_edges("validate_node", validate_route)

memory = InMemorySaver()
chat = graph.compile(checkpointer=memory)

print("\n" + "=" * 70)
print("✅ LANGGRAPH COMPILED SUCCESSFULLY")
print("=" * 70)
print("Graph Structure:")
print("  START → classifier_node")
print("    ├→ domain_search_node → rag_node → validate_node")
print("    ├→ summarize_node → rag_node → validate_node")
print("    ├→ compare_node → rag_node → validate_node")
print("    └→ general_search_node → validate_node")
print("  validate_node → [END | rag_node retry]")
print("=" * 70 + "\n")


def ask_chat(question: str, settings: Settings, conversation_id: str = "conversation_1"):
    """
    Main entry point for chat interactions.

    Executes the complete RAG workflow using the 5 formal Tools:

    1. Tool 1 (classify_intent): Classify user intent
    2. Tool 2 (semantic_search): Retrieve relevant documents
    3. Tool 4 (generate_grounded_answer): Generate answer with citations
    4. Tool 5 (validate_answer): Assess answer quality

    Plus conditional retry logic through LangGraph routing.

    Returns:
        ChatResponse with answer, citations, trace, and full metadata
    """
    import time

    start_time = time.time()

    config = {"configurable": {"thread_id": conversation_id}}

    # Initial state
    initial_messages = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "tool_traces": {},
    }

    print(f"\n{_RED}{'='*70}{_RESET}")
    print(f"{_RED}[CHAT] Starting workflow for: {question[:60]}...{_RESET}")
    print(f"{_RED}{'='*70}{_RESET}\n")

    # Execute graph
    state_output = chat.invoke(initial_messages, config=config)

    # Extract results
    response = state_output["messages"][-1].content
    intent_real = state_output.get("intent", "generalSearch")
    citations_list = state_output.get("documentos_recuperados", [])
    tool_traces_raw = state_output.get("tool_traces", {})
    validation_result = state_output.get("validation_result", {})

    # Build request ID
    request_id = f"req-{conversation_id}"

    # Build structured workflow trace from raw tool traces
    tools_used = list(tool_traces_raw.keys())
    trace_steps = []

    for tool_name, trace_data in tool_traces_raw.items():
        step = ToolTraceStep(
            tool_name=tool_name,
            status="success" if not trace_data.get("error") else "failure",
            input=trace_data.get("input", {}),
            output=trace_data.get("output", {}),
            error=trace_data.get("error"),
            timestamp=trace_data.get("timestamp"),
        )
        trace_steps.append(step)

    # Build workflow trace
    workflow_trace = WorkflowTrace(
        conversation_id=conversation_id,
        total_steps=len(trace_steps),
        tools_used=tools_used,
        tool_traces=trace_steps,
        validation_passed=validation_result.get("is_valid", False),
        validation_details={
            "coherence_score": validation_result.get("coherence_score", 0),
            "grounding_score": validation_result.get("grounding_score", 0),
            "hallucination_detected": validation_result.get("hallucination_detected", False),
            "completeness_score": validation_result.get("completeness_score", 0),
            "reason": validation_result.get("reason", ""),
        },
        execution_time_ms=round((time.time() - start_time) * 1000, 2),
    )

    print(f"\n{_RED}{'='*70}{_RESET}")
    print(f"{_RED}[CHAT] Workflow complete{_RESET}")
    print(f"{_RED}  Intent: {intent_real}{_RESET}")
    print(f"{_RED}  Tools Used: {', '.join(tools_used)}{_RESET}")
    print(f"{_RED}  Citations: {len(citations_list)}{_RESET}")
    print(f"{_RED}  Valid: {validation_result.get('is_valid', False)}{_RESET}")
    print(f"{_RED}  Time: {workflow_trace.execution_time_ms}ms{_RESET}")
    print(f"{_RED}{'='*70}{_RESET}\n")

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
        ),
        workflow_trace=workflow_trace,
        # Additional metadata for backward compatibility
        metadata={
            "tool_traces": tool_traces_raw,
            "validation_score": validation_result.get("grounding_score", 0),
            "hallucination_detected": validation_result.get("hallucination_detected", False),
        },
    )
