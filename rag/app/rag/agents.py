from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import Field
from typing_extensions import TypedDict

from app.api.schemas import ChatResponse, Trace
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.config import Settings

classifier_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ classifier_LLM listo:", classifier_LLM.model_name)

classifier_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
     You are a classifier. Your tasks is to classifier the user intention
     choose:
     - 'domainSearch' if the user is asking about Colombian Labor Laws
     - 'summarize' if the user is asking to summarize a document from the Colombian Labor Law domain (e.g.: a law article, a law)
     - 'compare' if the user is asking to compare two or more documents from the Colombian Labor Law domain
     - 'generalSearch' if the user is asking a general question
     Answer only with the JSOM scheme asked.
    """,
        ),
        ("user", "question: {question}"),
    ]
)

general_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
     Answer the user question in Spanish. At the end of the answer, add a note that says:

     **Nota:** Soy un asistente especializado en derecho laboral colombiano. Esta respuesta se proporciona a nivel general y puede no reflejar información actualizada o especializada sobre este tema. Se recomienda consultar una fuente experta o profesional en el área correspondiente.
    """,
        ),
        ("user", "question: {question}"),
    ]
)


class QuestionState(TypedDict):
    question: str


class ClassifyState(TypedDict):
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )


class ResponseState(TypedDict):
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"] = Field(
        description="User intent."
    )
    response: str


classifier_chain = classifier_prompt | classifier_LLM.with_structured_output(ClassifyState)
general_chain = general_prompt | classifier_LLM


def classifier(state: QuestionState):
    question = state["question"]
    classification = classifier_chain.invoke({"question": question})
    return {"question": classification["question"], "intent": classification["intent"]}


def general_search(state: ClassifyState):
    question = state["question"]
    res = general_chain.invoke({"question": question})
    print("GENERAL SEARCH RESULT:", res)

    return {"response": res.content}


def rag(state: ClassifyState):
    question = state["question"]
    intent = state["intent"]
    print("RAG REQUEST RESULT:", question, intent)

    res = classifier_LLM.invoke(f"Say which intent is this one: {intent}")

    return {"response": res.content}


def classify_route(state: ClassifyState) -> Literal["rag", "general_search"]:
    intent = state["intent"]
    return "general_search" if intent == "generalSearch" else "rag"


graph = StateGraph(ResponseState)

graph.add_node("classifier", classifier)
graph.add_node("general_search", general_search)
graph.add_node("rag", rag)

graph.add_edge(START, "classifier")
graph.add_conditional_edges("classifier", classify_route)
graph.add_edge("rag", END)
graph.add_edge("general_search", END)

chat = graph.compile()


def ask_chat(question: str, settings: Settings):
    response = chat.invoke({"question": question})["response"]
    print(type(response))
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
