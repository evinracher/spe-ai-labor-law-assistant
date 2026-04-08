"""
tests/test_kg.py
----------------
Tests for the Knowledge Graph (GraphDB/SPARQL) integration.

Covers:
  - graphdb connector (mocked)
  - graph_retriever SPARQL generation & formatting
  - query_knowledge_graph tool
  - rag_node graph context injection

Run with:
    make test-kg
    # or
    .venv/bin/pytest tests/test_kg.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

# ================================================================
# app.db.graphdb — connector unit tests
# ================================================================


class TestGraphDBConnector:
    """Tests for the SPARQL connector module."""

    def test_get_sparql_endpoint_creates_singleton(self):
        """Endpoint is created once and reused."""
        import app.db.graphdb as mod

        mod._sparql = None  # reset singleton

        with patch.object(mod, "settings") as mock_settings:
            mock_settings.GRAPHDB_URL = "http://localhost:7200"
            mock_settings.GRAPHDB_REPOSITORY = "test-repo"
            mock_settings.GRAPHDB_USERNAME = None
            mock_settings.GRAPHDB_PASSWORD = None

            ep1 = mod.get_sparql_endpoint()
            ep2 = mod.get_sparql_endpoint()
            assert ep1 is ep2

        mod._sparql = None  # cleanup

    def test_get_sparql_endpoint_sets_credentials_when_provided(self):
        """Credentials are passed to SPARQLWrapper when username/password are set."""
        import app.db.graphdb as mod

        mod._sparql = None

        with (
            patch.object(mod, "settings") as mock_settings,
            patch.object(mod, "SPARQLWrapper") as MockSPARQL,
        ):
            mock_settings.GRAPHDB_URL = "http://localhost:7200"
            mock_settings.GRAPHDB_REPOSITORY = "test-repo"
            mock_settings.GRAPHDB_USERNAME = "admin"
            mock_settings.GRAPHDB_PASSWORD = "secret"

            mock_instance = MagicMock()
            MockSPARQL.return_value = mock_instance

            mod.get_sparql_endpoint()
            mock_instance.setCredentials.assert_called_once_with("admin", "secret")

        mod._sparql = None

    def test_execute_sparql_returns_parsed_bindings(self):
        """execute_sparql converts raw SPARQL JSON response to list of dicts."""
        import app.db.graphdb as mod

        fake_response = {
            "results": {
                "bindings": [
                    {"name": {"type": "literal", "value": "Ana López"}},
                    {"name": {"type": "literal", "value": "Bruno Díaz"}},
                ]
            }
        }

        mock_sparql = MagicMock()
        mock_sparql.query.return_value.convert.return_value = fake_response

        with patch.object(mod, "get_sparql_endpoint", return_value=mock_sparql):
            results = mod.execute_sparql("SELECT ?name WHERE { ?s :nombreCompleto ?name }")

        assert len(results) == 2
        assert results[0] == {"name": "Ana López"}
        assert results[1] == {"name": "Bruno Díaz"}

    def test_execute_sparql_returns_empty_on_error(self):
        """execute_sparql returns [] and logs when the query fails."""
        import app.db.graphdb as mod

        mock_sparql = MagicMock()
        mock_sparql.query.side_effect = Exception("connection refused")

        with patch.object(mod, "get_sparql_endpoint", return_value=mock_sparql):
            results = mod.execute_sparql("SELECT ?x WHERE { ?x a :Persona }")

        assert results == []


# ================================================================
# app.rag.graph_retriever — retrieval layer tests
# ================================================================


class TestGraphRetriever:
    """Tests for SPARQL generation, template selection, and result formatting."""

    def test_format_graph_results_empty(self):
        from app.rag.graph_retriever import format_graph_results

        assert format_graph_results([]) == ""

    def test_format_graph_results_produces_readable_output(self):
        from app.rag.graph_retriever import format_graph_results

        rows = [
            {"nombre": "Ana López", "salario": "6500000.00"},
            {"nombre": "Bruno Díaz", "salario": "4200000.00"},
        ]
        output = format_graph_results(rows)

        assert "CONTEXTO ESTRUCTURADO DEL KNOWLEDGE GRAPH" in output
        assert "Ana López" in output
        assert "Bruno Díaz" in output
        assert "Resultado 1" in output
        assert "Resultado 2" in output

    def test_format_strips_ontology_prefix(self):
        from app.rag.graph_retriever import format_graph_results

        rows = [{"clase": "http://example.org/contratos#Empleado"}]
        output = format_graph_results(rows)
        assert ":Empleado" in output
        assert "http://example.org" not in output

    def test_select_template_matches_employees(self):
        from app.rag.graph_retriever import _select_template

        assert _select_template("Lista todos los empleados") == "all_employees"
        assert _select_template("listar trabajadores") == "all_employees"

    def test_select_template_matches_contracts(self):
        from app.rag.graph_retriever import _select_template

        assert _select_template("todos los contratos activos") == "all_contracts"

    def test_select_template_matches_employers(self):
        from app.rag.graph_retriever import _select_template

        assert _select_template("lista de empresas empleadores") == "all_employers"

    def test_select_template_matches_ontology(self):
        from app.rag.graph_retriever import _select_template

        assert _select_template("estructura de la ontología") == "ontology_classes"
        assert _select_template("muéstrame el esquema") == "ontology_classes"

    def test_select_template_returns_none_for_unmatched(self):
        from app.rag.graph_retriever import _select_template

        assert _select_template("¿Cuántos días de vacaciones tengo?") is None

    def test_generate_sparql_uses_template_when_available(self):
        from app.rag.graph_retriever import generate_sparql

        mock_llm = MagicMock()
        query = generate_sparql("Lista todos los empleados", mock_llm)

        assert query is not None
        assert "SELECT" in query
        assert ":Empleado" in query
        # LLM should NOT have been called since a template matched.
        mock_llm.invoke.assert_not_called()

    def test_generate_sparql_calls_llm_for_custom_question(self):
        from app.rag.graph_retriever import generate_sparql

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = (
            "PREFIX : <http://example.org/contratos#>\nSELECT ?x WHERE { ?x a :Empleado } LIMIT 5"
        )
        mock_llm.invoke.return_value = mock_response

        query = generate_sparql("¿Cuál es el salario de Ana López?", mock_llm)

        assert query is not None
        assert "SELECT" in query
        mock_llm.invoke.assert_called_once()

    def test_generate_sparql_returns_none_for_no_sparql(self):
        from app.rag.graph_retriever import generate_sparql

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "NO_SPARQL"
        mock_llm.invoke.return_value = mock_response

        query = generate_sparql("¿Cuál es la capital de Francia?", mock_llm)
        assert query is None

    def test_generate_sparql_strips_markdown_fences(self):
        from app.rag.graph_retriever import generate_sparql

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "```sparql\nSELECT ?x WHERE { ?x a :Persona } LIMIT 5\n```"
        mock_llm.invoke.return_value = mock_response

        query = generate_sparql("dame todas las personas", mock_llm)
        assert query is not None
        assert "```" not in query
        assert "SELECT" in query

    def test_query_graph_disabled(self):
        from app.rag.graph_retriever import query_graph

        mock_llm = MagicMock()
        with patch("app.rag.graph_retriever.settings") as mock_settings:
            mock_settings.GRAPHDB_ENABLED = False
            result = query_graph("algo", mock_llm)

        assert result["source"] == "graphdb_disabled"
        assert result["results"] == []

    def test_query_graph_end_to_end(self):
        """Full pipeline: generate SPARQL (template) → execute → format."""
        from app.rag.graph_retriever import query_graph

        fake_rows = [
            {"nombre": "Ana López", "puesto": "Desarrollador Senior"},
        ]
        mock_llm = MagicMock()

        with (
            patch("app.rag.graph_retriever.settings") as mock_settings,
            patch("app.rag.graph_retriever.execute_sparql", return_value=fake_rows),
        ):
            mock_settings.GRAPHDB_ENABLED = True
            result = query_graph("Lista todos los empleados", mock_llm)

        assert result["source"] == "graphdb"
        assert len(result["results"]) == 1
        assert "Ana López" in result["context"]


# ================================================================
# app.rag.tools — query_knowledge_graph tool test
# ================================================================


class TestKnowledgeGraphTool:
    """Tests for the query_knowledge_graph LangChain tool."""

    def test_tool_returns_disabled_when_graphdb_off(self):
        from app.rag.tools import query_knowledge_graph

        with patch("app.rag.tools.settings") as mock_settings:
            mock_settings.GRAPHDB_ENABLED = False
            result = query_knowledge_graph.invoke({"question": "test"})

        assert result["source"] == "graphdb_disabled"
        assert result["total_results"] == 0

    def test_tool_returns_results_from_graph(self):
        """Verify the tool delegates to query_graph and returns structured output."""
        from app.rag.graph_retriever import query_graph

        fake_graph_result = {
            "sparql_query": "SELECT ...",
            "results": [{"nombre": "Ana López"}],
            "context": "CONTEXTO ESTRUCTURADO...",
            "source": "graphdb",
        }

        mock_llm = MagicMock()

        with (
            patch("app.rag.graph_retriever.settings") as mock_settings,
            patch(
                "app.rag.graph_retriever.execute_sparql", return_value=fake_graph_result["results"]
            ),
            patch("app.rag.graph_retriever.generate_sparql", return_value="SELECT ..."),
        ):
            mock_settings.GRAPHDB_ENABLED = True

            result = query_graph("¿Quiénes trabajan en Empresa Alfa?", mock_llm)

        assert result["source"] == "graphdb"
        assert len(result["results"]) == 1
        assert result["results"][0]["nombre"] == "Ana López"

    def test_tool_handles_exception_gracefully(self):
        from app.rag.tools import query_knowledge_graph

        with patch("app.rag.tools.settings") as mock_settings:
            mock_settings.GRAPHDB_ENABLED = True
            with (
                patch("app.rag.graph_retriever.query_graph", side_effect=Exception("boom")),
                patch("app.rag.llm.get_llm", return_value=MagicMock()),
            ):
                result = query_knowledge_graph.invoke({"question": "test"})

        assert result["total_results"] == 0
        assert "error" in result
