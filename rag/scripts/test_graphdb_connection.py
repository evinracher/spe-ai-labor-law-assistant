"""
scripts/test_graphdb_connection.py
----------------------------------
Live connectivity test for the GraphDB instance configured in .env.

Verifies:
  1. The SPARQL endpoint is reachable.
  2. Authentication works (if credentials are set).
  3. The repository contains data (counts triples).
  4. A sample SPARQL query returns results.

Usage:
    make test-graphdb
    # or
    .venv/bin/python -m scripts.test_graphdb_connection
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (rag/) is on sys.path so we can import app.*
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.graphdb import execute_sparql, get_sparql_endpoint  # noqa: E402

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

PASS = f"{_GREEN}✔ PASS{_RESET}"
FAIL = f"{_RED}✘ FAIL{_RESET}"
WARN = f"{_YELLOW}⚠ WARN{_RESET}"


def _header(title: str) -> None:
    print(f"\n{_BOLD}{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}{_RESET}")


def main() -> None:
    _header("GraphDB Live Connection Test")

    print(f"  GRAPHDB_URL        = {settings.GRAPHDB_URL}")
    print(f"  GRAPHDB_REPOSITORY = {settings.GRAPHDB_REPOSITORY}")
    print(f"  GRAPHDB_USERNAME   = {'(set)' if settings.GRAPHDB_USERNAME else '(not set)'}")
    print(f"  GRAPHDB_ENABLED    = {settings.GRAPHDB_ENABLED}")

    if not settings.GRAPHDB_ENABLED:
        print(f"\n  {WARN}  GRAPHDB_ENABLED is false — nothing to test.")
        sys.exit(0)

    failures = 0

    # ── Test 1: Endpoint reachable ──────────────────────────────────
    _header("1. SPARQL Endpoint Reachable")
    try:
        ep = get_sparql_endpoint()
        print(f"  Endpoint: {ep.endpoint}")
        print(f"  {PASS}  SPARQLWrapper configured successfully.")
    except Exception as exc:
        print(f"  {FAIL}  Could not configure endpoint: {exc}")
        failures += 1
        # No point continuing if the endpoint itself fails.
        _summary(failures)
        sys.exit(1)

    # ── Test 2: Simple ASK query (authentication + connectivity) ────
    _header("2. Connectivity & Authentication (ASK query)")
    try:
        results = execute_sparql("SELECT (1 AS ?alive) WHERE {}")
        if results and results[0].get("alive") == "1":
            print(f"  {PASS}  Server responded correctly.")
        else:
            print(f"  {FAIL}  Unexpected response: {results}")
            failures += 1
    except Exception as exc:
        print(f"  {FAIL}  Query failed: {exc}")
        failures += 1
        _summary(failures)
        sys.exit(1)

    # ── Test 3: Count triples in the repository ─────────────────────
    _header("3. Triple Count")
    try:
        count_query = "SELECT (COUNT(*) AS ?total) WHERE { ?s ?p ?o }"
        results = execute_sparql(count_query)
        total = int(results[0]["total"]) if results else 0
        if total > 0:
            print(f"  Total triples: {_GREEN}{total}{_RESET}")
            print(f"  {PASS}  Repository contains data.")
        else:
            print(f"  {WARN}  Repository is empty (0 triples). Did you load the ontology?")
    except Exception as exc:
        print(f"  {FAIL}  Count query failed: {exc}")
        failures += 1

    # ── Test 4: List OWL classes ────────────────────────────────────
    _header("4. OWL Classes in Ontology")
    try:
        classes_query = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?clase ?label
            WHERE {
                ?clase a owl:Class .
                OPTIONAL { ?clase rdfs:label ?label . }
            }
            LIMIT 25
        """
        results = execute_sparql(classes_query)
        if results:
            print(f"  Found {len(results)} class(es):")
            for row in results:
                label = row.get("label", "")
                clase = row.get("clase", "").replace("http://example.org/contratos#", ":")
                print(f"    • {clase}  {f'({label})' if label else ''}")
            print(f"  {PASS}  Ontology classes retrieved.")
        else:
            print(f"  {WARN}  No OWL classes found. Is the ontology loaded?")
    except Exception as exc:
        print(f"  {FAIL}  Classes query failed: {exc}")
        failures += 1

    # ── Test 5: Sample instance query ───────────────────────────────
    _header("5. Sample Instances (Employees)")
    try:
        instances_query = """
            PREFIX : <http://example.org/contratos#>
            SELECT ?nombre ?puesto
            WHERE {
                ?emp a :Empleado ;
                     :nombreCompleto ?nombre .
                OPTIONAL { ?emp :ocupaPuesto ?p . ?p :tituloPuesto ?puesto . }
            }
            LIMIT 10
        """
        results = execute_sparql(instances_query)
        if results:
            print(f"  Found {len(results)} employee(s):")
            for row in results:
                puesto = row.get("puesto", "N/A")
                print(f"    • {row['nombre']}  —  {puesto}")
            print(f"  {PASS}  Instance data retrieved.")
        else:
            print(f"  {WARN}  No employees found. Are instances loaded?")
    except Exception as exc:
        print(f"  {FAIL}  Instances query failed: {exc}")
        failures += 1

    _summary(failures)
    sys.exit(1 if failures else 0)


def _summary(failures: int) -> None:
    _header("Summary")
    if failures == 0:
        print(f"  {_GREEN}{_BOLD}All checks passed. GraphDB is ready.{_RESET}")
    else:
        print(f"  {_RED}{_BOLD}{failures} check(s) failed.{_RESET}")


if __name__ == "__main__":
    main()
