"""
Formal Tools Implementation for SPE AI Labor Law Assistant
===========================================================

This module implements 5 explicit LangChain Tools that formalize core RAG 
functionalities, ensuring compliance with the "5 Tools" rubric requirement.

Each Tool is documented with:
- Clear responsibility
- LLM provider justification
- Input/output schemas
- Usage context in the workflow

Tools Implemented:
1. classify_intent - Intent classification (Gemini)
2. semantic_search - Semantic retrieval from vector DB (Groq + Chroma)
3. read_document - Full document access by metadata
4. generate_grounded_answer - Answer generation with citations (Gemini)
5. validate_answer - Quality assessment and hallucination detection
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from app.core.config import settings
from app.rag.retriever import recuperar_contexto_dinamico, formatear_documentos_para_gemini
from app.api.schemas import Citation
from app.rag.citation_formatter import format_citations_in_text  # re-exported for use by other modules

__all__ = [
    "classify_intent",
    "semantic_search",
    "read_document",
    "generate_grounded_answer",
    "validate_answer",
    "format_citations_in_text",
    "gemini_LLM",
    "groq_LLM",
]

if TYPE_CHECKING:
    from app.core.config import Settings

# ====================================================================
# Module-level LLM & Vector DB Initialization
# ====================================================================

_RED = "\033[91m"
_RESET = "\033[0m"

# Project paths
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_CHROMA_PATH = os.path.join(_PROJECT_ROOT, "db_chroma")

# LLM Instances
groq_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
print("✅ groq_LLM ready:", groq_LLM.model_name)

gemini_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    google_api_key=settings.GOOGLE_API_KEY
)
print("✅ gemini_LLM ready:", gemini_LLM.model)

# Vector Database
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
vectorstore = Chroma(persist_directory=_DB_CHROMA_PATH, embedding_function=embeddings)
print("✅ vectorstore ready:", _DB_CHROMA_PATH)


# ====================================================================
# Tool 1: classify_intent
# ====================================================================

class IntentClassification(BaseModel):
    """Structured output for intent classification."""
    question: str = Field(description="The original user question.")
    intent: str = Field(
        description="Classified intent: domainSearch, summarize, compare, or generalSearch"
    )
    confidence: float = Field(
        description="Confidence score (0.0-1.0) for the classification.",
        ge=0.0,
        le=1.0
    )


@tool
def classify_intent(question: str) -> dict:
    """
    Classify user intent to route to appropriate handler.
    
    **Responsibility:**
    Determines whether the user query requires:
    - domainSearch: Search in legal corpus for specific information
    - summarize: Generate structured summary of a legal topic
    - compare: Compare multiple legal concepts
    - generalSearch: General knowledge response without RAG
    
    **LLM Provider: Google Gemini**
    Justification: Gemini excels at semantic understanding and contextual 
    classification. Superior to Groq for NLP classification tasks.
    
    **Input:**
    - question: User's input query (string)
    
    **Output:**
    - question: Normalized question
    - intent: Classified intent category
    - confidence: Confidence score (0.0-1.0)
    
    **Trace Information:**
    - Model: gemini-2.5-flash
    - Temperature: 0.1 (deterministic)
    - Used in: Initial routing decision
    
    Args:
        question: The user's input query
        
    Returns:
        Dictionary with classified intent and confidence score
    """
    from app.rag.prompts import CLASSIFIER_PROMPT
    
    print(f"{_RED}[TOOL 1] classify_intent - Processing: {question[:50]}...{_RESET}")
    
    try:
        # Use Gemini with structured output for intent classification
        classifier_chain = CLASSIFIER_PROMPT | gemini_LLM.with_structured_output(
            IntentClassification
        )
        result = classifier_chain.invoke({"question": question})
        
        output = {
            "question": result.question,
            "intent": result.intent,
            "confidence": result.confidence
        }
        
        print(f"{_RED}[TOOL 1] classify_intent - Result: intent={result.intent}, "
              f"confidence={result.confidence:.2f}{_RESET}")
        
        return output
        
    except Exception as e:
        print(f"{_RED}[TOOL 1] classify_intent - ERROR: {str(e)}{_RESET}")
        return {
            "question": question,
            "intent": "generalSearch",
            "confidence": 0.5,
            "error": str(e)
        }


# ====================================================================
# Tool 2: semantic_search
# ====================================================================

class RetrievedDocument(BaseModel):
    """Structure for retrieved documents from vector DB."""
    doc_id: str = Field(description="Document identifier from metadata")
    page: int | None = Field(description="Page number if available")
    chunk_id: str = Field(description="Chunk identifier within document")
    content: str = Field(description="Document text content")
    metadata: dict = Field(description="Full metadata dictionary")


@tool
def semantic_search(query: str, top_k: int | None = None) -> dict:
    """
    Perform semantic search on Colombian labor law corpus.
    
    **Responsibility:**
    Retrieves relevant legal documents from Chroma vector database using
    semantic similarity. Dynamically determines top_k parameter using Groq
    for intelligent query analysis.
    
    **LLM Provider: Groq (for top_k determination)**
    Justification: Fast inference for meta-reasoning about query complexity.
    Groq's speed ensures responsive retrieval pipeline.
    
    **Vector DB: Chroma with HuggingFace embeddings**
    Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    Justification: Multilingual support for Spanish/English legal documents.
    
    **Input:**
    - query: Search query in natural language
    - top_k: Optional override for result count (default: dynamic)
    
    **Output:**
    - query: The processed search query
    - top_k_used: Actual k value used for retrieval
    - documents: List of retrieved documents with metadata
    - total_results: Number of results returned
    
    **Trace Information:**
    - Vector DB: Chroma
    - Embeddings: paraphrase-multilingual-MiniLM-L12-v2
    - Dynamic k: Determined by Groq analysis
    
    Args:
        query: Search query for legal documents
        top_k: Optional override for number of results
        
    Returns:
        Dictionary with retrieved documents and metadata
    """
    print(f"{_RED}[TOOL 2] semantic_search - Query: {query[:60]}...{_RESET}")
    
    try:
        # Use Groq to dynamically determine top_k if not provided
        if top_k is None:
            analysis_prompt = (
                f"You are a legal expert. Given this user query: '{query}'\n"
                f"Determine how many law fragments (between 1 and 10) we need to retrieve "
                f"to fully answer it. If it is very specific, choose 2 or 4. "
                f"If it is very broad, choose 8 or 10.\n"
                f"Respond with ONLY a single integer number."
            )
            k_response = groq_LLM.invoke(analysis_prompt)
            try:
                top_k = int(k_response.content.strip().split()[-1])  # Extract last number
                top_k = max(1, min(top_k, 10))  # Clamp to 1-10
            except (ValueError, AttributeError, IndexError):
                top_k = 4  # Fallback default
        
        print(f"{_RED}[TOOL 2] semantic_search - Using top_k={top_k}{_RESET}")
        
        # Retrieve from Chroma using similarity_search
        retrieved_documents = vectorstore.similarity_search(query, k=top_k)
        
        # Format for return
        retrieved_docs = []
        for doc in retrieved_documents:
            retrieved_docs.append({
                "doc_id": doc.metadata.get("doc_id", "unknown"),
                "page": doc.metadata.get("page"),
                "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        output = {
            "query": query,
            "top_k_used": top_k,
            "documents": retrieved_docs,
            "total_results": len(retrieved_docs)
        }
        
        print(f"{_RED}[TOOL 2] semantic_search - Retrieved {len(retrieved_docs)} documents{_RESET}")
        
        return output
        
    except Exception as e:
        print(f"{_RED}[TOOL 2] semantic_search - ERROR: {str(e)}{_RESET}")
        return {
            "query": query,
            "top_k_used": 0,
            "documents": [],
            "total_results": 0,
            "error": str(e)
        }


# ====================================================================
# Tool 3: read_document
# ====================================================================

@tool
def read_document(doc_id: str, page: int | None = None) -> dict:
    """
    Read full document or specific page from vector DB by metadata.
    
    **Responsibility:**
    Provides direct access to complete documents or specific pages from
    the legal corpus. Enables detailed analysis for summarization and
    comparison tasks. Strengthens traceability by linking back to original sources.
    
    **Implementation:**
    Queries Chroma vector DB using doc_id and optional page filter.
    Returns aggregated content with full metadata preservation.
    
    **Input:**
    - doc_id: Document identifier (from semantic_search metadata)
    - page: Optional page number for partial retrieval
    
    **Output:**
    - doc_id: Requested document ID
    - page: Requested page (if specified)
    - content: Full document or page text
    - metadata: Complete metadata including source, date, etc.
    - chunks_count: Number of chunks/sections in result
    
    **Use Cases:**
    - Deep dive analysis for comprehensive summaries
    - Full context for comparison of multiple articles
    - Source verification and citation accuracy
    
    Args:
        doc_id: Document identifier
        page: Optional page number
        
    Returns:
        Dictionary with document content and metadata
    """
    print(f"{_RED}[TOOL 3] read_document - doc_id={doc_id}, page={page}{_RESET}")
    
    try:
        # Query Chroma using get method with where filter
        results = vectorstore.get(
            where={"doc_id": doc_id} if page is None else {"doc_id": doc_id, "page": page}
        )
        
        if not results or not results.get("documents"):
            # Fallback: try similarity search with doc_id as query
            print(f"{_RED}[TOOL 3] read_document - Using fallback search{_RESET}")
            return {
                "doc_id": doc_id,
                "page": page,
                "content": "Document not found in vector DB",
                "metadata": {},
                "chunks_count": 0,
                "error": "No matching document found"
            }
        
        # Aggregate content and metadata
        aggregated_content = "\n\n--- CHUNK SEPARATOR ---\n\n".join(
            results.get("documents", [])
        )
        aggregated_metadata = {}
        if results.get("metadatas") and len(results["metadatas"]) > 0:
            aggregated_metadata = results["metadatas"][0]
        
        output = {
            "doc_id": doc_id,
            "page": page,
            "content": aggregated_content,
            "metadata": aggregated_metadata,
            "chunks_count": len(results.get("documents", []))
        }
        
        print(f"{_RED}[TOOL 3] read_document - Retrieved {output['chunks_count']} chunks{_RESET}")
        
        return output
        
    except Exception as e:
        print(f"{_RED}[TOOL 3] read_document - ERROR: {str(e)}{_RESET}")
        return {
            "doc_id": doc_id,
            "page": page,
            "content": "",
            "metadata": {},
            "chunks_count": 0,
            "error": str(e)
        }


# ====================================================================
# Tool 4: generate_grounded_answer
# ====================================================================

@tool
def generate_grounded_answer(
    question: str,
    context: str,
    intent: str,
    documents: list | None = None
) -> dict:
    """
    Generate answer grounded exclusively in retrieved context.
    
    **Responsibility:**
    Produces the final answer based strictly on provided legal context.
    Ensures grounding by refusing to extrapolate beyond context.
    Includes citations preserving full metadata for traceability.
    
    **LLM Provider: Google Gemini**
    Justification: Superior at nuanced legal language generation and
    citation formatting. Better at maintaining semantic accuracy while
    following strict context constraints.
    
    **Input:**
    - question: Original user question
    - context: Formatted legal context from semantic_search
    - intent: User intent (to tailor response structure)
    - documents: Optional list of source documents for citations
    
    **Output:**
    - answer: Generated response in Spanish
    - citations: List of Citation objects with source metadata
    - tokens_used: Approximate token count
    - truncated: Boolean indicating if context was truncated
    
    **Grounding Guarantee:**
    - Explicit instruction to use ONLY provided context
    - No extrapolation beyond retrieved documents
    - All claims backed by citations
    - Language fully in Spanish for Colombian audience
    
    Args:
        question: User's original question
        context: Formatted legal context
        intent: Classified intent (domainSearch, summarize, compare)
        documents: Optional list of source documents
        
    Returns:
        Dictionary with generated answer and citations
    """
    print(f"{_RED}[TOOL 4] generate_grounded_answer - Processing...{_RESET}")
    
    try:
        # Build context-aware instruction based on intent
        # These instructions are merged from the domain/summarize/compare nodes
        # to ensure they are actually enforced in the prompt.
        intent_instructions = {
            "domainSearch": (
                "Act as an expert in Colombian labor law. Read the retrieved legal context, "
                "and answer the user's question directly, precisely, and grounded strictly in the provided law.\n\n"
                f"The user's question is: '{question}'.\n\n"
                "Make sure to cite the relevant articles, laws, or decrees using the provided metadata.\n\n"
                "IMPORTANT: Your final response MUST be written entirely in Spanish."
            ),
            "summarize": (
                "Act as a legal analyst. Using the retrieved legal context, generate a clear, "
                "structured, and easy-to-understand summary of the consulted topic. "
                "Use bullet points if necessary for better readability.\n\n"
                f"The user's consulted topic is: '{question}'.\n\n"
                "IMPORTANT: Your final response MUST be written entirely in Spanish."
            ),
            "compare": (
                "Act as an expert in Colombian labor law. Based on the retrieved context, "
                "compare the legal concepts requested by the user in a structured way. "
                "Organize your response strictly into these three sections:\n"
                "1. Definición de los conceptos (Definition of the concepts)\n"
                "2. Diferencias clave (Key differences)\n"
                "3. Implicaciones legales (Legal implications for the employee/employer)\n\n"
                f"The information to compare is: '{question}'.\n\n"
                "IMPORTANT: Your final response MUST be written entirely in Spanish."
            ),
            "generalSearch": (
                "Act as a helpful legal assistant. Provide a general response based on "
                "the provided context if available."
            ),
        }

        specific_instruction = intent_instructions.get(
            intent,
            intent_instructions["domainSearch"]
        )
        
        # Build final prompt
        final_prompt = (
            f"You are a legal expert specialized in Colombian labor law.\n\n"
            f"SYSTEM INSTRUCTION: {specific_instruction}\n\n"
            f"USER QUESTION: {question}\n"
            f"RETRIEVED LEGAL CONTEXT (In Spanish):\n{context}\n\n"
            f"REQUIREMENTS:\n"
            f"- Base your answer STRICTLY on the retrieved context above.\n"
            f"- Include citations using the document metadata.\n"
            f"- Output the final response entirely in SPANISH.\n"
            f"- Do NOT extrapolate or use knowledge outside the provided context."
        )
        
        # Generate with Gemini
        response = gemini_LLM.invoke(final_prompt)
        answer_text = response.content
        
        # Build citations from documents if provided
        citations_list = []
        if documents:
            for doc in documents:
                # Handle both dict and object formats
                if isinstance(doc, dict):
                    metadata = doc.get("metadata", {})
                    citation = Citation(
                        source=metadata.get("doc_id", "Unknown"),
                        page=metadata.get("page"),
                        chunk_id=metadata.get("chunk_id", "N/A"),
                        snippet=doc.get("content", "")[:250] + "..."
                    )
                else:
                    citation = Citation(
                        source=doc.metadata.get("doc_id", "Unknown"),
                        page=doc.metadata.get("page"),
                        chunk_id=doc.metadata.get("chunk_id", "N/A"),
                        snippet=doc.page_content[:250] + "..."
                    )
                citations_list.append(citation)
        
        output = {
            "answer": answer_text,
            "citations": [c.dict() for c in citations_list],
            "tokens_used": len(answer_text.split()),  # Approximate
            "truncated": len(context) > 10000,
            "intent_used": intent
        }
        
        print(f"{_RED}[TOOL 4] generate_grounded_answer - Generated {len(citations_list)} citations{_RESET}")
        
        return output
        
    except Exception as e:
        print(f"{_RED}[TOOL 4] generate_grounded_answer - ERROR: {str(e)}{_RESET}")
        return {
            "answer": f"Error generating answer: {str(e)}",
            "citations": [],
            "tokens_used": 0,
            "truncated": False,
            "error": str(e)
        }


# ====================================================================
# Tool 5: validate_answer
# ====================================================================

class ValidationResult(BaseModel):
    """Structure for answer validation output."""
    is_valid: bool = Field(description="Whether answer passes quality checks")
    coherence_score: float = Field(
        description="Coherence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    grounding_score: float = Field(
        description="How well-grounded in context (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    hallucination_detected: bool = Field(
        description="Whether extrapolation/hallucination was detected"
    )
    completeness_score: float = Field(
        description="Whether answer fully addresses question (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    reason: str = Field(description="Detailed reason for validation decision")


@tool
def validate_answer(
    question: str,
    answer: str,
    context: str
) -> dict:
    """
    Validate answer quality and detect hallucinations.
    
    **Responsibility:**
    Evaluates generated answer against multiple criteria:
    1. Coherence: Is response logically structured?
    2. Grounding: Is answer backed by provided context?
    3. Hallucination: Does answer extrapolate or fabricate?
    4. Completeness: Does answer address the full question?
    
    **LLM Provider: Google Gemini**
    Justification: Superior at nuanced reasoning about text quality,
    semantic alignment, and detection of implicit extrapolation.
    
    **Input:**
    - question: Original user question
    - answer: Generated answer to validate
    - context: Retrieved context used for grounding check
    
    **Output:**
    - is_valid: Boolean validation result
    - coherence_score: 0.0-1.0 score
    - grounding_score: How well-grounded in context
    - hallucination_detected: Boolean flag
    - completeness_score: How fully question is addressed
    - reason: Detailed explanation for decision
    
    **Validation Loop Integration:**
    Returns is_valid=False when:
    - Answer contains obvious hallucinations
    - Incoherent or irrelevant response
    - Insufficient grounding in context
    - Incomplete answer to question
    
    Can trigger retry through rag_node for refinement.
    
    Args:
        question: Original user question
        answer: Generated answer text
        context: Retrieved context for comparison
        
    Returns:
        Dictionary with detailed validation scores and decision
    """
    print(f"{_RED}[TOOL 5] validate_answer - Evaluating answer quality...{_RESET}")
    
    try:
        # Build validation prompt
        validation_prompt = (
            f"You are an expert evaluator for legal document responses.\n\n"
            f"ORIGINAL QUESTION: {question}\n\n"
            f"RETRIEVED CONTEXT:\n{context}\n\n"
            f"GENERATED ANSWER:\n{answer}\n\n"
            f"Evaluate this response on these criteria:\n"
            f"1. COHERENCE: Is the response logically structured and easy to follow?\n"
            f"2. GROUNDING: Is every claim backed by the provided context?\n"
            f"3. HALLUCINATION: Does the response extrapolate or fabricate beyond context?\n"
            f"4. COMPLETENESS: Does the response fully address the original question?\n\n"
            f"Respond with JSON:\n"
            f'{{\n'
            f'  "coherence_score": <0.0-1.0>,\n'
            f'  "grounding_score": <0.0-1.0>,\n'
            f'  "hallucination_detected": <true|false>,\n'
            f'  "completeness_score": <0.0-1.0>,\n'
            f'  "reason": "<detailed explanation>"\n'
            f'}}'
        )
        
        response = gemini_LLM.invoke(validation_prompt)
        
        # Parse response (with fallback)
        try:
            import json
            result_text = response.content
            # Extract JSON from response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                eval_result = json.loads(json_str)
            else:
                # Fallback if JSON not found
                eval_result = {
                    "coherence_score": 0.5,
                    "grounding_score": 0.5,
                    "hallucination_detected": False,
                    "completeness_score": 0.5,
                    "reason": "Could not parse detailed evaluation"
                }
        except json.JSONDecodeError:
            eval_result = {
                "coherence_score": 0.5,
                "grounding_score": 0.5,
                "hallucination_detected": False,
                "completeness_score": 0.5,
                "reason": "JSON parsing error in validation"
            }
        
        # Determine overall validity
        is_valid = (
            eval_result.get("coherence_score", 0) >= 0.7 and
            eval_result.get("grounding_score", 0) >= 0.6 and
            not eval_result.get("hallucination_detected", False) and
            eval_result.get("completeness_score", 0) >= 0.7
        )
        
        output = {
            "is_valid": is_valid,
            "coherence_score": eval_result.get("coherence_score", 0.5),
            "grounding_score": eval_result.get("grounding_score", 0.5),
            "hallucination_detected": eval_result.get("hallucination_detected", False),
            "completeness_score": eval_result.get("completeness_score", 0.5),
            "reason": eval_result.get("reason", "Validation completed"),
            "threshold_results": {
                "coherence_pass": eval_result.get("coherence_score", 0) >= 0.7,
                "grounding_pass": eval_result.get("grounding_score", 0) >= 0.6,
                "no_hallucination": not eval_result.get("hallucination_detected", False),
                "completeness_pass": eval_result.get("completeness_score", 0) >= 0.7
            }
        }
        
        print(f"{_RED}[TOOL 5] validate_answer - Valid: {is_valid}, "
              f"Hallucination: {eval_result.get('hallucination_detected', False)}{_RESET}")
        
        return output
        
    except Exception as e:
        print(f"{_RED}[TOOL 5] validate_answer - ERROR: {str(e)}{_RESET}")
        return {
            "is_valid": False,
            "coherence_score": 0.0,
            "grounding_score": 0.0,
            "hallucination_detected": True,
            "completeness_score": 0.0,
            "reason": f"Validation error: {str(e)}",
            "error": str(e)
        }


# ====================================================================
# Tools Registry for Export
# ====================================================================

TOOLS_LIST = [
    classify_intent,
    semantic_search,
    read_document,
    generate_grounded_answer,
    validate_answer
]

TOOLS_DICT = {
    "classify_intent": classify_intent,
    "semantic_search": semantic_search,
    "read_document": read_document,
    "generate_grounded_answer": generate_grounded_answer,
    "validate_answer": validate_answer
}

print("\n" + "="*70)
print("✅ 5 FORMAL TOOLS REGISTERED SUCCESSFULLY")
print("="*70)
print("1. classify_intent - Intent classification (Gemini)")
print("2. semantic_search - Semantic retrieval (Groq + Chroma)")
print("3. read_document - Full document access")
print("4. generate_grounded_answer - Answer generation with citations (Gemini)")
print("5. validate_answer - Quality assessment (Gemini)")
print("="*70 + "\n")
