"""
app/db/graphdb.py
-----------------
GraphDB SPARQL connector.

Provides a thin wrapper around SPARQLWrapper to execute SPARQL queries
against the configured GraphDB repository.  The module exposes two helpers:

- ``get_sparql_endpoint()`` - returns a configured SPARQLWrapper instance.
- ``execute_sparql(query)`` - runs a SPARQL query and returns parsed results.
"""

from __future__ import annotations

import logging
from typing import Any

from SPARQLWrapper import BASIC, JSON, SPARQLWrapper

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton endpoint
# ---------------------------------------------------------------------------

_sparql: SPARQLWrapper | None = None


def get_sparql_endpoint() -> SPARQLWrapper:
    """Return a configured SPARQLWrapper pointing at the GraphDB SPARQL endpoint."""
    global _sparql
    if _sparql is None:
        endpoint_url = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"
        _sparql = SPARQLWrapper(endpoint_url)
        _sparql.setReturnFormat(JSON)
        if settings.GRAPHDB_USERNAME and settings.GRAPHDB_PASSWORD:
            _sparql.setHTTPAuth(BASIC)
            _sparql.setCredentials(settings.GRAPHDB_USERNAME, settings.GRAPHDB_PASSWORD)
            logger.info("GraphDB SPARQL endpoint configured with auth: %s", endpoint_url)
        else:
            logger.info("GraphDB SPARQL endpoint configured (no auth): %s", endpoint_url)
    return _sparql


def execute_sparql(query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL SELECT query and return a list of result-binding dicts.

    Each dict maps variable names to their string values.  For example::

        [{"clase": "Empleado", "label": "Empleado"},
         {"clase": "Contrato", "label": "Contrato"}]

    If the query fails, an empty list is returned and the error is logged.
    """
    sparql = get_sparql_endpoint()
    sparql.setQuery(query)

    try:
        response = sparql.query().convert()
    except Exception:
        logger.exception("SPARQL query failed")
        return []

    bindings: list[dict[str, Any]] = []
    for row in response.get("results", {}).get("bindings", []):
        bindings.append({var: row[var]["value"] for var in row})
    return bindings
