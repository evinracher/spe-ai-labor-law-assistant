"""
app/rag/graph_retriever.py
--------------------------
Knowledge Graph retrieval layer for the RAG pipeline.

This module translates natural-language questions into SPARQL queries
against the labor-law ontology stored in GraphDB, executes them, and
formats the results as structured context that can be combined with
the vector-store context inside the agent workflow.

Architecture:
  1. The LLM receives the ontology schema summary + the user question.
  2. It generates a SPARQL SELECT query.
  3. The query is executed via ``app.db.graphdb.execute_sparql``.
  4. Results are formatted as a human-readable context block.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.db.graphdb import execute_sparql

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ontology schema summary - fed to the LLM so it can write valid SPARQL.
# Keep this in sync with the actual ontology loaded in GraphDB.
# ---------------------------------------------------------------------------

ONTOLOGY_SCHEMA = """
PREFIX : <http://example.org/contratos#>

## Classes
# :Persona, :Contratante, :Contratista, :Empleador, :Empleado
# :Contrato, :ContratoLaboral, :ContratoPrestacionServicios
# :Puesto, :Salario, :Departamento, :JornadaLaboral, :Beneficio

## Object Properties
# :tieneContrato (Persona → Contrato)
# :contrataA / :esContratadoPor (Contratante ↔ Persona)
# :empleaA / :esEmpleadoDe (Empleador ↔ Empleado)
# :asignaPuesto (Empleador → Puesto)
# :ocupaPuesto (Empleado → Puesto)
# :perteneceADepartamento (Empleado → Departamento)
# :tieneSalario (Empleado → Salario)
# :tieneJornada (Empleado → JornadaLaboral)
# :ofreceBeneficio (Empleador → Beneficio)
# :recibeBeneficio (Empleado → Beneficio)
# :contratoAsociaEmpleado (ContratoLaboral → Empleado)
# :contratoAsociaEmpleador (ContratoLaboral → Empleador)
# :contratoAsociaContratista (ContratoPrestacionServicios → Contratista)
# :contratoAsociaContratante (ContratoPrestacionServicios → Contratante)

## Data Properties
# :nombreCompleto (Persona → xsd:string)
# :identificacion (Persona → xsd:string)
# :fechaInicio, :fechaFin (Contrato → xsd:date)
# :duracionMeses (Contrato → xsd:integer)
# :activo (Contrato → xsd:boolean)
# :salarioBase (Salario → xsd:decimal)
# :moneda (Salario → xsd:string)
# :tituloPuesto (Puesto → xsd:string)
# :horasSemanales (JornadaLaboral → xsd:integer)
# :tipoBeneficio (Beneficio → xsd:string)
# :nombreDepartamento (Departamento → xsd:string)
"""

SPARQL_GENERATION_PROMPT = """You are an expert SPARQL query generator for a Colombian labor-law ontology stored in GraphDB.

ONTOLOGY SCHEMA:
{schema}

RULES:
1. Generate ONLY a valid SPARQL SELECT query. No explanations, no markdown fences.
2. Always use the prefix  PREFIX : <http://example.org/contratos#>
3. Use OPTIONAL for properties that may not exist on every individual.
4. Add LIMIT 20 unless the question explicitly asks for all results.
5. Use FILTER with regex() for name-based lookups (case-insensitive with "i" flag).
6. Return useful variables (names, dates, amounts) — not just URIs.
7. If the question cannot be answered with this ontology, return exactly: NO_SPARQL

USER QUESTION:
{question}

SPARQL QUERY:"""


# ---------------------------------------------------------------------------
# Predefined SPARQL templates for common query patterns
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, str] = {
    "all_employees": """
        PREFIX : <http://example.org/contratos#>
        SELECT ?nombre ?puesto ?departamento ?salario ?jornada
        WHERE {
            ?emp a :Empleado ;
                 :nombreCompleto ?nombre .
            OPTIONAL { ?emp :ocupaPuesto ?p . ?p :tituloPuesto ?puesto . }
            OPTIONAL { ?emp :perteneceADepartamento ?d . ?d :nombreDepartamento ?departamento . }
            OPTIONAL { ?emp :tieneSalario ?s . ?s :salarioBase ?salario . }
            OPTIONAL { ?emp :tieneJornada ?j . ?j :horasSemanales ?jornada . }
        }
        LIMIT 20
    """,
    "all_contracts": """
        PREFIX : <http://example.org/contratos#>
        SELECT ?tipo ?empleado ?empleador ?inicio ?fin ?activo ?duracion
        WHERE {
            ?c a :Contrato .
            OPTIONAL { ?c a :ContratoLaboral . BIND("Laboral" AS ?tipo) }
            OPTIONAL { ?c a :ContratoPrestacionServicios . BIND("Prestación de Servicios" AS ?tipo_ps) }
            BIND(COALESCE(?tipo, ?tipo_ps, "Desconocido") AS ?tipo)
            OPTIONAL { ?c :contratoAsociaEmpleado ?e . ?e :nombreCompleto ?empleado . }
            OPTIONAL { ?c :contratoAsociaContratista ?ct . ?ct :nombreCompleto ?empleado . }
            OPTIONAL { ?c :contratoAsociaEmpleador ?er . ?er :nombreCompleto ?empleador . }
            OPTIONAL { ?c :contratoAsociaContratante ?cte . ?cte :nombreCompleto ?empleador . }
            OPTIONAL { ?c :fechaInicio ?inicio . }
            OPTIONAL { ?c :fechaFin ?fin . }
            OPTIONAL { ?c :activo ?activo . }
            OPTIONAL { ?c :duracionMeses ?duracion . }
        }
        LIMIT 20
    """,
    "all_employers": """
        PREFIX : <http://example.org/contratos#>
        SELECT ?nombre ?identificacion (GROUP_CONCAT(DISTINCT ?beneficio; separator=", ") AS ?beneficios)
        WHERE {
            ?emp a :Empleador ;
                 :nombreCompleto ?nombre .
            OPTIONAL { ?emp :identificacion ?identificacion . }
            OPTIONAL { ?emp :ofreceBeneficio ?b . ?b :tipoBeneficio ?beneficio . }
        }
        GROUP BY ?nombre ?identificacion
        LIMIT 20
    """,
    "ontology_classes": """
        PREFIX : <http://example.org/contratos#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?clase ?label ?superClase
        WHERE {
            ?clase a owl:Class .
            OPTIONAL { ?clase rdfs:label ?label . }
            OPTIONAL { ?clase rdfs:subClassOf ?superClase .
                       FILTER(ISIRI(?superClase)) }
        }
        LIMIT 50
    """,
}


def _select_template(question: str) -> str | None:
    """Return a predefined SPARQL template key if the question matches a common pattern."""
    q = question.lower()
    if re.search(r"(todos|lista|listar).*(empleados|trabajadores)", q):
        return "all_employees"
    if re.search(r"(todos|lista|listar).*(contratos)", q):
        return "all_contracts"
    if re.search(r"(todos|lista|listar).*(empleadores|empresas)", q):
        return "all_employers"
    if re.search(r"(clases|estructura|ontolog[ií]a|esquema)", q):
        return "ontology_classes"
    return None


# ---------------------------------------------------------------------------
# Core public API
# ---------------------------------------------------------------------------


def generate_sparql(question: str, llm: BaseChatModel) -> str | None:
    """Use the LLM to translate a natural-language question into SPARQL.

    Returns ``None`` when the LLM determines the question cannot be answered
    by the ontology (i.e. it returns ``NO_SPARQL``).
    """
    # 1. Try predefined templates first (cheaper, no LLM call).
    template_key = _select_template(question)
    if template_key:
        logger.info("Using predefined SPARQL template: %s", template_key)
        return _TEMPLATES[template_key]

    # 2. LLM-generated query.
    prompt = SPARQL_GENERATION_PROMPT.format(schema=ONTOLOGY_SCHEMA, question=question)
    response = llm.invoke(prompt)
    raw = response.content.strip() if hasattr(response, "content") else str(response).strip()

    # Strip markdown code fences if the LLM wraps the query.
    raw = re.sub(r"^```(?:sparql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    if "NO_SPARQL" in raw.upper():
        return None

    return raw


def query_graph(question: str, llm: BaseChatModel) -> dict[str, Any]:
    """End-to-end knowledge graph retrieval.

    1. Generates a SPARQL query from the question (template or LLM).
    2. Executes it against GraphDB.
    3. Returns a dict with the query, raw results, and a formatted context string.
    """
    if not settings.GRAPHDB_ENABLED:
        return {
            "sparql_query": None,
            "results": [],
            "context": "",
            "source": "graphdb_disabled",
        }

    sparql = generate_sparql(question, llm)

    if sparql is None:
        return {
            "sparql_query": None,
            "results": [],
            "context": "",
            "source": "not_applicable",
        }

    results = execute_sparql(sparql)

    context = format_graph_results(results, sparql)

    return {
        "sparql_query": sparql,
        "results": results,
        "context": context,
        "source": "graphdb",
    }


def format_graph_results(results: list[dict[str, Any]], sparql_query: str = "") -> str:
    """Format SPARQL result bindings into a readable context block for the LLM."""
    if not results:
        return ""

    lines = ["CONTEXTO ESTRUCTURADO DEL KNOWLEDGE GRAPH (GraphDB/SPARQL):\n"]

    # Use the variable names from the first result as column headers.
    headers = list(results[0].keys())

    for i, row in enumerate(results, 1):
        row_parts = []
        for h in headers:
            value = row.get(h, "")
            # Strip the ontology prefix for readability.
            if isinstance(value, str) and "http://example.org/contratos#" in value:
                value = value.replace("http://example.org/contratos#", ":")
            row_parts.append(f"  {h}: {value}")
        lines.append(f"--- Resultado {i} ---")
        lines.extend(row_parts)
        lines.append("")

    return "\n".join(lines)
