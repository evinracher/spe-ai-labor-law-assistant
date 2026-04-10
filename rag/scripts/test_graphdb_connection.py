"""
scripts/test_graphdb_connection.py
----------------------------------
Live connectivity and SPARQL test suite for the GraphDB instance configured
in .env.  All queries are executed via RDFLib (ConjunctiveGraph +
SPARQLUpdateStore), satisfying the following requirements:

  1. SELECT basic           — lists all OWL classes in the repository.
  2. SELECT + FILTER        — employees whose base salary exceeds a threshold.
  3. SELECT + ORDER BY      — contracts sorted by start date (desc).
  4. SELECT + LIMIT         — first N instances of any type.
  5. UPDATE - INSERT DATA   — inserts a test employee into the graph.
  6. UPDATE - DELETE DATA   — removes the previously inserted test employee.

Usage:
    make test-graphdb
    # or
    .venv/bin/python -m scripts.test_graphdb_connection
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure the project root (rag/) is on sys.path so we can import app.*
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from rdflib import ConjunctiveGraph  # noqa: E402
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore  # noqa: E402

from app.core.config import settings  # noqa: E402

# ── Namespace prefix used throughout the ontology ──────────────────────────
_BASE = "http://example.org/contratos#"

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

PASS = f"{_GREEN}✔ PASS{_RESET}"
FAIL = f"{_RED}✘ FAIL{_RESET}"
WARN = f"{_YELLOW}⚠ WARN{_RESET}"


# ---------------------------------------------------------------------------
# RDFLib helpers
# ---------------------------------------------------------------------------


def _build_graph() -> ConjunctiveGraph:
    """Return a ConjunctiveGraph backed by GraphDB via SPARQLUpdateStore."""
    query_ep = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"
    update_ep = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}/statements"

    auth: tuple[str, str] | None = None
    if settings.GRAPHDB_USERNAME and settings.GRAPHDB_PASSWORD:
        auth = (settings.GRAPHDB_USERNAME, settings.GRAPHDB_PASSWORD)

    store = SPARQLUpdateStore(
        queryEndpoint=query_ep,
        update_endpoint=update_ep,
        auth=auth,
    )
    return ConjunctiveGraph(store=store)


def _run_select(g: ConjunctiveGraph, query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL SELECT and return a list of {var: value} dicts."""
    results = []
    for row in g.query(query):
        results.append(
            {str(var): (str(val) if val is not None else None) for var, val in zip(row.labels, row)}
        )
    return results


def _run_update(g: ConjunctiveGraph, update: str) -> None:
    """Execute a SPARQL UPDATE statement against the store."""
    g.update(update)


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------


def _header(title: str) -> None:
    print(f"\n{_BOLD}{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}{_RESET}")


def _summary(failures: int) -> None:
    _header("Summary")
    if failures == 0:
        print(f"  {_GREEN}{_BOLD}All checks passed. GraphDB is ready.{_RESET}")
    else:
        print(f"  {_RED}{_BOLD}{failures} check(s) failed.{_RESET}")


# ---------------------------------------------------------------------------
# Main test flow
# ---------------------------------------------------------------------------


def main() -> None:
    _header("GraphDB — SPARQL Test Suite with RDFLib")

    print(f"  GRAPHDB_URL        = {settings.GRAPHDB_URL}")
    print(f"  GRAPHDB_REPOSITORY = {settings.GRAPHDB_REPOSITORY}")
    print(f"  GRAPHDB_USERNAME   = {'(set)' if settings.GRAPHDB_USERNAME else '(not set)'}")
    print(f"  GRAPHDB_ENABLED    = {settings.GRAPHDB_ENABLED}")

    if not settings.GRAPHDB_ENABLED:
        print(f"\n  {WARN}  GRAPHDB_ENABLED is false — nothing to test.")
        sys.exit(0)

    failures = 0

    # ── Initialise RDFLib graph ─────────────────────────────────────
    _header("0. Connection — SPARQLUpdateStore (RDFLib)")
    try:
        g = _build_graph()
        print(f"  {PASS}  ConjunctiveGraph with SPARQLUpdateStore configured.")
    except Exception as exc:
        print(f"  {FAIL}  Could not initialise RDFLib graph: {exc}")
        _summary(1)
        sys.exit(1)

    # ── Test 1: Basic SELECT ────────────────────────────────────────
    # Retrieves all OWL classes defined in the repository.
    _header("1. SELECT — OWL Classes (basic query)")
    try:
        q = """
            PREFIX owl:  <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?clase ?etiqueta
            WHERE {
                ?clase a owl:Class .
                OPTIONAL { ?clase rdfs:label ?etiqueta . }
            }
        """
        rows = _run_select(g, q)
        if rows:
            print(f"  Found {len(rows)} class(es):")
            for r in rows:
                label = r.get("etiqueta", "")
                clase = r.get("clase", "").replace(_BASE, ":")
                print(f"    • {clase}  {f'({label})' if label else ''}")
            print(f"  {PASS}  Basic SELECT executed successfully.")
        else:
            print(f"  {WARN}  No classes found. Is the ontology loaded?")
    except Exception as exc:
        print(f"  {FAIL}  Query failed: {exc}")
        failures += 1

    # ── Test 2: SELECT + FILTER ─────────────────────────────────────
    # Retrieves employees whose base salary exceeds the defined threshold.
    _header("2. SELECT + FILTER — Employees with salary >= 3,000,000 COP")
    try:
        q = """
            PREFIX :    <http://example.org/contratos#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?nombre ?salarioBase
            WHERE {
                ?emp  a            :Empleado ;
                      :nombreCompleto ?nombre ;
                      :tieneSalario   ?sal .
                ?sal  :salarioBase    ?salarioBase .
                FILTER (?salarioBase >= 3000000)
            }
        """
        rows = _run_select(g, q)
        if rows:
            print("  Employees with salary >= 3,000,000:")
            for r in rows:
                print(f"    • {r.get('nombre')}  —  {r.get('salarioBase')} COP")
            print(f"  {PASS}  SELECT + FILTER executed successfully.")
        else:
            print(f"  {WARN}  No employee exceeds the threshold (or no instances loaded).")
            print(f"  {PASS}  SELECT + FILTER executed without errors.")
    except Exception as exc:
        print(f"  {FAIL}  Query failed: {exc}")
        failures += 1

    # ── Test 3: SELECT + ORDER BY ───────────────────────────────────
    # Lists labor contracts sorted by start date (descending).
    _header("3. SELECT + ORDER BY — Labor contracts by date (desc)")
    try:
        q = """
            PREFIX :    <http://example.org/contratos#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?contrato ?fechaInicio ?duracion
            WHERE {
                ?contrato a             :ContratoLaboral ;
                          :fechaInicio  ?fechaInicio .
                OPTIONAL { ?contrato :duracionMeses ?duracion . }
            }
            ORDER BY DESC(?fechaInicio)
        """
        rows = _run_select(g, q)
        if rows:
            print(f"  {len(rows)} labor contract(s) found:")
            for r in rows:
                c = r.get("contrato", "").replace(_BASE, ":")
                dur = r.get("duracion", "N/A")
                print(f"    • {c}  start={r.get('fechaInicio')}  duration={dur} month(s)")
            print(f"  {PASS}  SELECT + ORDER BY executed successfully.")
        else:
            print(f"  {WARN}  No labor contracts found (or no instances loaded).")
            print(f"  {PASS}  SELECT + ORDER BY executed without errors.")
    except Exception as exc:
        print(f"  {FAIL}  Query failed: {exc}")
        failures += 1

    # ── Test 4: SELECT + LIMIT ──────────────────────────────────────
    # Returns the first 5 instances of any type in the graph.
    _header("4. SELECT + LIMIT — First 5 instances in the graph")
    try:
        q = """
            SELECT DISTINCT ?sujeto ?tipo
            WHERE {
                ?sujeto a ?tipo .
            }
            LIMIT 5
        """
        rows = _run_select(g, q)
        if rows:
            for r in rows:
                s = r.get("sujeto", "").replace(_BASE, ":")
                t = r.get("tipo", "").replace(_BASE, ":")
                print(f"    • {s}  rdf:type  {t}")
            print(f"  {PASS}  SELECT + LIMIT executed successfully.")
        else:
            print(f"  {WARN}  The repository appears to be empty.")
            print(f"  {PASS}  SELECT + LIMIT executed without errors.")
    except Exception as exc:
        print(f"  {FAIL}  Query failed: {exc}")
        failures += 1

    # ── Test 5: UPDATE — INSERT DATA ────────────────────────────────
    # Inserts a test employee into the graph.
    _header("5. UPDATE (INSERT DATA) — Insert test employee")
    try:
        insert_q = """
            PREFIX :    <http://example.org/contratos#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            INSERT DATA {
                :EmpleadoTest a              :Empleado ;
                              :nombreCompleto "Empleado De Prueba"^^xsd:string ;
                              :identificacion "TEST-001"^^xsd:string .
            }
        """
        _run_update(g, insert_q)

        # Verify the triple was actually inserted
        verify_q = """
            PREFIX : <http://example.org/contratos#>
            SELECT ?nombre ?id
            WHERE {
                :EmpleadoTest :nombreCompleto ?nombre ;
                              :identificacion ?id .
            }
        """
        rows = _run_select(g, verify_q)
        if rows:
            r = rows[0]
            print(f"  Triple inserted: name={r.get('nombre')}  id={r.get('id')}")
            print(f"  {PASS}  UPDATE INSERT DATA executed successfully.")
        else:
            print(f"  {FAIL}  Triple not found after INSERT.")
            failures += 1
    except Exception as exc:
        print(f"  {FAIL}  UPDATE INSERT DATA failed: {exc}")
        failures += 1

    # ── Test 6: UPDATE — DELETE DATA ────────────────────────────────
    # Removes the test employee inserted in the previous test.
    _header("6. UPDATE (DELETE DATA) — Remove test employee")
    try:
        delete_q = """
            PREFIX :    <http://example.org/contratos#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            DELETE DATA {
                :EmpleadoTest a              :Empleado ;
                              :nombreCompleto "Empleado De Prueba"^^xsd:string ;
                              :identificacion "TEST-001"^^xsd:string .
            }
        """
        _run_update(g, delete_q)

        # Verify the triple was removed
        verify_q = """
            PREFIX : <http://example.org/contratos#>
            SELECT ?nombre
            WHERE {
                :EmpleadoTest :nombreCompleto ?nombre .
            }
        """
        rows = _run_select(g, verify_q)
        if not rows:
            print("  Triple :EmpleadoTest removed successfully.")
            print(f"  {PASS}  UPDATE DELETE DATA executed successfully.")
        else:
            print(f"  {FAIL}  Triple still present after DELETE.")
            failures += 1
    except Exception as exc:
        print(f"  {FAIL}  UPDATE DELETE DATA failed: {exc}")
        failures += 1

    _summary(failures)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
