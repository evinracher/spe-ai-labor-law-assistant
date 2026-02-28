# Informe Técnico — Asistente de Derecho Laboral Colombiano (RAG)

**Proyecto:** SPE AI Labor Law Assistant  
**Versión:** 1.0  
**Fecha:** 28 de febrero de 2026  
**Tecnología base:** LangGraph · ChromaDB · Gemini 2.5 Flash · Groq llama-3.1-8b-instant · FastAPI · React

---

## Tabla de Contenidos

1. [Descripción general del sistema](#1-descripción-general-del-sistema)  
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)  
3. [Herramientas implementadas (7 Tools)](#3-herramientas-implementadas-7-tools)  
4. [Justificación de la selección de modelos LLM](#4-justificación-de-la-selección-de-modelos-llm)  
5. [Diseño del grafo LangGraph](#5-diseño-del-grafo-langgraph)  
6. [Pipeline de ingesta de documentos](#6-pipeline-de-ingesta-de-documentos)  
7. [API REST — Esquemas de solicitud y respuesta](#7-api-rest--esquemas-de-solicitud-y-respuesta)  
8. [Interfaz de usuario (Chat UI)](#8-interfaz-de-usuario-chat-ui)  
9. [Casos de uso documentados](#9-casos-de-uso-documentados)  
10. [Registros de ejecución](#10-registros-de-ejecución)  
11. [Conclusiones](#11-conclusiones)

---

## 1. Descripción general del sistema

El **Asistente de Derecho Laboral Colombiano** es un chatbot conversacional basado en la arquitectura **Retrieval-Augmented Generation (RAG)**. Su objetivo es responder preguntas sobre la legislación laboral colombiana de forma precisa, trazable y fundamentada en documentos legales reales, además de poder responder consultas generales.

### Capacidades principales

| Capacidad | Descripción |
|-----------|-------------|
| Búsqueda legal semántica | Recupera fragmentos relevantes del corpus legal usando similitud vectorial |
| Resumen legal | Genera resúmenes estructurados de artículos y normas laborales |
| Comparación legal | Compara conceptos jurídicos en formato estructurado de tres secciones |
| Consulta general | Responde preguntas fuera del dominio laboral usando el LLM directamente |
| Citas y trazabilidad | Retorna fuentes citadas con documento, página y fragmento exactos |
| Validación de respuestas | Evalúa la calidad y fundamentación de cada respuesta antes de entregarla |
| Gestión de conversación | Mantiene historial de mensajes por sesión usando `InMemorySaver` de LangGraph |

---

## 2. Arquitectura del sistema

### 2.1 Visión de componentes

```
┌─────────────────────────────────┐
│          React Chat UI          │  Vite + TypeScript + TailwindCSS
└───────────────┬─────────────────┘
                │ POST /chat (JSON)
┌───────────────▼─────────────────┐
│       FastAPI  (uvicorn)        │  Python 3.11+
│  - POST /chat  - GET /health    │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────┐
│                      LangGraph StateGraph                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    classifier_node                           │   │
│  │           (Gemini con ClassifierOutput structured)           │   │
│  └────────┬──────────────┬──────────────┬──────────────┬────────┘   │
│           │              │              │              │            │
│    domainSearch     summarize       compare      generalSearch      │
│           │              │              │              │            │
│           └──────────────┼──────────────┘              │            │
│                          ▼                             │            │
│  ┌───────────────────────────────────────┐             │            │
│  │              rag_node                 │             │            │
│  │    (Solo retrieval - ChromaDB)        │             │            │
│  │    Recupera contexto → NO genera      │             │            │
│  └────────┬──────────────┬───────────────┘             │            │
│           │              │                              │            │
│           ▼              ▼                              │            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │            │
│  │domain_search│  │ summarize_  │  │  compare_   │     │            │
│  │   _node     │  │   node      │  │   node      │     │            │
│  │  (ReAct)    │  │  (ReAct)    │  │  (ReAct)    │     │            │
│  │  4 tools    │  │  3 tools    │  │  3 tools    │     │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │            │
│         └────────────────┼────────────────┘            │            │
│                          │                             │            │
│                          │         ┌───────────────────▼──────┐     │
│                          │         │   general_search_node    │     │
│                          │         │      (Groq directo)      │     │
│                          │         │      Sin RAG/tools       │     │
│                          │         └───────────────────┬──────┘     │
│                          └─────────────────────────────┤            │
│                                                        ▼            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      validate_node                            │  │
│  │                        (ReAct)                                │  │
│  │          Tools: verify_citation_exists, check_law_vigency     │  │
│  └────────────────────────────┬──────────────────────────────────┘  │
│                               │                                     │
│                    ┌──────────┴──────────┐                          │
│                    │                     │                          │
│               is_valid=True        is_valid=False                   │
│                    │                (max 1 retry)                   │
│                   END                    │                          │
│                               volver a expert_node                  │
└─────────────────────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────┐
│   ChromaDB (persistente local)  │
│  Google gemini-embedding-001    │
│  task_type: RETRIEVAL_DOCUMENT  │
└─────────────────────────────────┘
```

### 2.2 Pila tecnológica

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Orquestación de agentes | LangGraph StateGraph + ReAct Agents | 0.2.0+ |
| LLM primario | Google Gemini 2.5 Flash | API v1 |
| LLM secundario | Groq llama-3.1-8b-instant | API v1 |
| Base de datos vectorial | ChromaDB | local persistente |
| Embeddings | Google `gemini-embedding-001` | API v1 |
| API Backend | FastAPI + Uvicorn | Python 3.11+ |
| Frontend | React 18 + TypeScript + Vite | Node 18+ |
| UI Components | Radix UI + Material UI + Tailwind CSS | — |

---

## 3. Herramientas implementadas (7 Tools)

Todas las herramientas se implementan como `@tool` de LangChain en el módulo `rag/app/rag/tools.py`. Los agentes ReAct (usando `create_agent`) deciden autónomamente cuáles herramientas usar según la consulta.

### Principio de Least Privilege

Cada nodo del grafo tiene acceso solo a las herramientas que necesita:

| Nodo | Herramientas disponibles |
|------|-------------------------|
| `domain_search_node` | list_laws_by_topic, search_by_law_number, get_article_text, find_related_jurisprudence |
| `summarize_node` | list_laws_by_topic, get_article_text, get_document_metadata |
| `compare_node` | list_laws_by_topic, search_by_law_number, get_article_text |
| `validate_node` | verify_citation_exists, check_law_vigency |

---

### Tool 1 — `list_laws_by_topic`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (acceso directo a ChromaDB)

**Responsabilidad:** Lista las leyes y decretos relacionados con un tema específico. Realiza búsqueda semántica y agrupa los resultados por documento fuente.

**Esquema de entrada:**

```python
{
    "topic": str,           # Tema a buscar (ej: "despido", "vacaciones")
    "max_results": int      # Máximo de leyes únicas (default: 10)
}
```

**Casos de uso:**
- "Qué leyes hablan sobre pensiones"
- "Normatividad sobre acoso laboral"
- "Leyes de maternidad y paternidad"

---

### Tool 2 — `search_by_law_number`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (filtro de metadatos en ChromaDB)

**Responsabilidad:** Busca fragmentos de una ley específica por su número o nombre. Filtra directamente en los metadatos del documento por coincidencia exacta.

**Esquema de entrada:**

```python
{
    "law_identifier": str,  # Número o nombre (ej: "Ley 100", "Decreto 1072")
    "max_results": int      # Fragmentos a retornar (default: 5)
}
```

**Casos de uso:**
- "Dame los artículos de la Ley 100 de 1993"
- "Busca en el Decreto 1072"
- "Qué dice el Código Sustantivo del Trabajo"

---

### Tool 3 — `get_article_text`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (búsqueda semántica + regex)

**Responsabilidad:** Obtiene el texto completo de un artículo específico de una ley. Usa búsqueda semántica optimizada combinando el número de artículo con el contexto de la ley.

**Esquema de entrada:**

```python
{
    "article_number": str,  # Número del artículo (ej: "64", "127")
    "law_name": str         # Nombre de la ley (opcional)
}
```

**Casos de uso:**
- "Artículo 64 del CST" (indemnización por despido)
- "Artículo 127 del Código Sustantivo" (definición de salario)
- "Dame el artículo 306" (prima de servicios)

---

### Tool 4 — `get_document_metadata`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (acceso directo a ChromaDB)

**Responsabilidad:** Obtiene los metadatos completos de un documento sin cargar el contenido. Útil para conocer la estructura del documento antes de leerlo.

**Esquema de salida:**

```python
{
    "doc_id": str,
    "found": bool,
    "total_chunks": int,
    "total_pages": int,
    "pages": list,
    "chunk_ids": list
}
```

---

### Tool 5 — `find_related_jurisprudence`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (búsqueda semántica con filtro)

**Responsabilidad:** Busca sentencias y jurisprudencia relacionada a un tema legal. Filtra por documentos que contengan términos típicos de jurisprudencia (sentencia, corte, tutela, etc.)

**Esquema de entrada:**

```python
{
    "legal_topic": str,     # Tema legal a buscar jurisprudencia
    "max_results": int      # Máximo de sentencias (default: 5)
}
```

**Casos de uso:**
- "Jurisprudencia sobre estabilidad laboral reforzada"
- "Sentencias de la Corte sobre despido sin justa causa"
- "Tutelas sobre acoso laboral"

---

### Tool 6 — `verify_citation_exists`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (búsqueda semántica + regex)

**Responsabilidad:** Herramienta anti-alucinación. Verifica que una citación legal (Ley X, Artículo Y) existe realmente en el corpus.

**Esquema de entrada:**

```python
{
    "law_name": str,        # Nombre de la ley citada
    "article_number": str   # Número de artículo citado
}
```

**Esquema de salida:**

```python
{
    "citation_verified": bool,
    "source_document": str | None,
    "matching_excerpt": str | None,
    "confidence": "high" | "not_found"
}
```

---

### Tool 7 — `check_law_vigency`

**Archivo:** `rag/app/rag/tools.py`  
**Sin LLM** (base de datos de referencia)

**Responsabilidad:** Verifica si una ley o decreto está vigente y si ha sido modificado. Consulta una base de datos de referencia con el estado de las principales normas laborales colombianas.

**Base de vigencias incluida:**

```python
LAW_VIGENCY_DB = {
    "ley 100 de 1993": {"vigente": True, "modificada_por": ["Ley 797 de 2003", "Ley 860 de 2003"]},
    "codigo sustantivo del trabajo": {"vigente": True, "modificada_por": ["Múltiples reformas"]},
    "ley 50 de 1990": {"vigente": True, "modificada_por": []},
    "decreto 1072 de 2015": {"vigente": True, "modificada_por": ["Decreto 1563 de 2016"]},
    "ley 1010 de 2006": {"vigente": True, "modificada_por": []},  # Acoso laboral
    "ley 2101 de 2021": {"vigente": True, "modificada_por": []},  # Reducción jornada laboral
    ...
}
```

**Esquema de salida:**

```python
{
    "law_name": str,
    "found_in_db": bool,
    "vigente": bool | None,
    "modificada_por": list,
    "recommendation": str
}
```

---

## 4. Justificación de la selección de modelos LLM

### 4.1 Google Gemini 2.5 Flash

**Modelo:** `gemini-2.5-flash`  
**Proveedor:** Google AI

Gemini 2.5 Flash fue seleccionado para los agentes que requieren **razonamiento semántico complejo, comprensión contextual profunda y generación de texto estructurado en español**. Sus ventajas frente a alternativas son:

| Criterio | Justificación |
|----------|--------------|
| **Comprensión multilingüe nativa** | Gemini fue entrenado con corpus masivos en español, lo que resulta en mejor calidad lexical y sintáctica para respuestas legales en español colombiano |
| **Razonamiento legal** | Capacidad superior para seguir instrucciones complejas de rol (experto legal, analista, evaluador) y mantener consistencia en respuestas estructuradas |
| **Salida estructurada (`with_structured_output`)** | Soporte robusto para `Pydantic BaseModel` en clasificación de intenciones con campos tipados (`question`, `intent`, `confidence`) |
| **Velocidad adecuada** | La variante Flash ofrece latencia menor que Gemini Pro manteniendo calidad suficiente para el contexto de uso |
| **Validación de alucinaciones** | Capacidad destacada para evaluar si el texto generado está fundamentado en el contexto provisto, tarea crítica para Tool 5 |

**Agentes donde se usa Gemini:**

- **`classifier_node`:** Clasificación semántica de intenciones con salida estructurada Pydantic (`ClassifierOutput`)
- **`domain_search_node`:** Agente ReAct que genera respuesta con acceso a 4 tools de búsqueda legal
- **`summarize_node`:** Agente ReAct para generar resúmenes estructurados con 3 tools
- **`compare_node`:** Agente ReAct para comparaciones con formato de 3 secciones
- **`validate_node`:** Agente ReAct que verifica citaciones y vigencia de leyes

### 4.2 Groq llama-3.1-8b-instant

**Modelo:** `llama-3.1-8b-instant`  
**Proveedor:** Groq

Groq fue seleccionado específicamente para las tareas de **meta-razonamiento rápido y análisis de consultas** donde la velocidad de inferencia es crítica. Sus ventajas son:

| Criterio | Justificación |
|----------|--------------|
| **Velocidad de inferencia** | Groq ofrece inferencia a través de hardware especializado (LPU — Language Processing Unit), resultando en latencias de 10–50x menores que soluciones basadas en GPU convencional |
| **Costo por token** | Significativamente más económico para llamadas frecuentes de bajo contexto como determinar el valor `top_k` |
| **Análisis rápido de consultas** | El modelo `llama-3.1-8b-instant` es suficientemente capaz para razonar sobre la complejidad de una consulta y devolver un entero (1–10), sin necesitar el poder completo de Gemini |
| **Complementariedad** | Libera a Gemini para las tareas computacionalmente intensas (generación, clasificación semántica, validación) mientras Groq maneja decisiones simples de meta-análisis |

**Agentes donde se usa Groq:**

- **`general_search_node`:** Respuestas directas para consultas fuera del dominio laboral (sin RAG)
- **`retriever.py` — `recuperar_contexto_dinamico`:** Determina el `k_value` (1–10) antes de lanzar la búsqueda en ChromaDB con salida estructurada (`KSelector`)

### 4.3 Google Embeddings (gemini-embedding-001)

**Modelo:** `models/gemini-embedding-001`  
**Proveedor:** Google AI  
**Task Type:** `RETRIEVAL_DOCUMENT`

Los embeddings de Google fueron seleccionados para la indexación y búsqueda vectorial en ChromaDB:

| Criterio | Justificación |
|----------|--------------|
| **Consistencia con LLM** | Usar embeddings del mismo proveedor (Google) que el LLM principal garantiza mejor alineación semántica |
| **Soporte nativo español** | Entrenado con corpus multilinges incluyendo español jurídico |
| **Task type específico** | `RETRIEVAL_DOCUMENT` optimiza los vectores para búsqueda de documentos |
| **Integración directa** | `GoogleGenerativeAIEmbeddings` de LangChain se integra nativamente con ChromaDB |

**Configuración:**

```python
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="RETRIEVAL_DOCUMENT",
    google_api_key=settings.GOOGLE_API_KEY
)
vectorstore = Chroma(persist_directory=_DB_CHROMA_PATH, embedding_function=embeddings)
```

---

## 5. Diseño del grafo LangGraph

### 5.1 Arquitectura ReAct

El sistema usa **agentes ReAct** (`create_agent` de LangChain) en lugar de lógica pre-cableada. Cada nodo experto decide autónomamente qué herramientas usar basado en la pregunta y el contexto disponible.

### 5.2 Nodos del grafo

| Nodo | Tipo | Herramientas | Descripción |
|------|------|--------------|-------------|
| `classifier_node` | Clasificación | — (Gemini structured) | Clasifica la intención con `ClassifierOutput` |
| `rag_node` | Retrieval | — (ChromaDB directo) | Solo recupera contexto, NO genera respuesta |
| `domain_search_node` | ReAct Generation | 4 tools | Genera respuesta para búsquedas legales |
| `summarize_node` | ReAct Generation | 3 tools | Genera resúmenes estructurados |
| `compare_node` | ReAct Generation | 3 tools | Genera comparaciones con 3 secciones |
| `general_search_node` | LLM directo | — (Groq) | Responde sin RAG usando Groq |
| `validate_node` | ReAct Validation | 2 tools | Verifica citaciones y vigencia |

### 5.3 Flujo de ejecución (Option C Architecture)

```
START
  └─► classifier_node  [Gemini con ClassifierOutput]
        │
        ├───── domainSearch ─────────┐
        ├───── summarize ────────────┤
        ├───── compare ──────────────┤
        │                             ▼
        │                    rag_node  [Solo retrieval - ChromaDB]
        │                             │
        │                             ▼
        │            ┌───────────────────────────────────┐
        │            │ route_to_expert (condicional)     │
        │            ├─────────┬───────────┬───────────┤
        │            ▼           ▼           ▼           │
        │   domain_search_  summarize_  compare_node   │
        │       node        node        (ReAct+3tools) │
        │   (ReAct+4tools) (ReAct+3tools)              │
        │            │           │           │         │
        │            └─────────┼───────────┘         │
        │                      ▼                       │
        └─ generalSearch ──► general_search_node (Groq) │
                             │                        │
                             └────────────────────────┘
                                       ▼
                              validate_node [ReAct+2tools]
                                       │
                    ┌────────────┴────────────┐
                    │                         │
              is_valid=True           is_valid=False (max 1 retry)
                    │                         │
                   END               volver a expert_node
```

### 5.4 Estado del grafo (`GraphState`)

```python
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    instruccion_especifica: str          # Instrucción del nodo de intención
    contexto_legal: str                  # Contexto recuperado de rag_node
    laws_hint: str                       # Leyes detectadas por list_laws_by_topic
    is_valid: bool                       # Decisión de validación
    documentos_recuperados: list         # Documentos con metadatos para citas
```

### 5.5 Memoria conversacional

El grafo usa `InMemorySaver` de LangGraph como `checkpointer`. Cada sesión se identifica con un `thread_id` (= `conversation_id` en la API). Esto permite mantener el historial de mensajes entre turnos.

Además, se implementa `_build_conversation_history()` que extrae los últimos 5 turnos del historial y los inyecta en el prompt de cada agente ReAct.

```python
memory = InMemorySaver()
chat = graph.compile(checkpointer=memory)

# Configuración por sesión
config = {"configurable": {"thread_id": conversation_id}}
state_output = chat.invoke(initial_messages, config=config)
```

---

## 6. Pipeline de ingesta de documentos

**Archivo:** `rag/app/rag/ingestion.py`  
**Script de ejecución:** `rag/app/rag/pipelines/run_ingestion.py`

### 6.1 Etapas del pipeline

```
PDF
 │
 ├─ 1. Carga ───── PyPDFLoader
 │
 ├─ 2. Limpieza ── limpiar_texto()
 │                  ├── Reducir múltiples saltos de línea
 │                  ├── Reducir espacios múltiples
 │                  └── Eliminar caracteres nulos (\x00)
 │
 ├─ 3. Fragmentación ── RecursiveCharacterTextSplitter
 │                        ├── chunk_size=1000
 │                        ├── chunk_overlap=150
 │                        └── separators: ["\nARTÍCULO", "\nPARÁGRAFO",
 │                                         "\nCAPÍTULO", "\nTÍTULO",
 │                                         "\n\n", "\n", " ", ""]
 │
 ├─ 4. Enriquecimiento de metadatos
 │       ├── chunk_id: "chunk_{i}"
 │       └── doc_id: fuente del archivo (ruta del PDF)
 │
 └─ 5. Indexación ── Chroma.from_documents()
                      ├── Embeddings: GoogleGenerativeAIEmbeddings
                      │   (gemini-embedding-001, task_type: RETRIEVAL_DOCUMENT)
                      └── persist_directory: ./db_chroma
```

### 6.2 Justificación de separadores

Los separadores `\nARTÍCULO`, `\nPARÁGRAFO`, `\nCAPÍTULO`, `\nTÍTULO` son específicos para la estructura del Código Sustantivo del Trabajo colombiano y otras normas legales, garantizando que los fragmentos respeten la integridad de los artículos y no los corten arbitrariamente.

### 6.3 Justificación del modelo de embeddings

El modelo `gemini-embedding-001` de Google fue seleccionado porque:
- **Consistencia semántica:** Usar embeddings del mismo proveedor que el LLM principal garantiza mejor alineación
- **Soporte nativo español:** Entrenado con corpus multilingües incluyendo español jurídico
- **Task type específico:** `RETRIEVAL_DOCUMENT` optimiza los vectores para búsqueda de documentos
- **Integración directa:** `GoogleGenerativeAIEmbeddings` de LangChain se integra nativamente con ChromaDB

---

## 7. API REST — Esquemas de solicitud y respuesta

### 7.1 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Verificación de liveness del servidor |
| `POST` | `/chat` | Consulta al asistente de derecho laboral |

### 7.2 Solicitud `POST /chat`

```json
{
  "question": "¿Cuántos días de vacaciones tiene un trabajador en Colombia?",
  "conversation_id": "sesion-123",
  "max_citations": 5
}
```

### 7.3 Respuesta `POST /chat`

```json
{
  "ok": true,
  "request_id": "req-sesion-123",
  "answer": "Según el Código Sustantivo del Trabajo...",
  "citations": [
    {
      "source": "CST_codigo_sustantivo_trabajo.pdf",
      "page": 45,
      "chunk_id": "chunk_132",
      "snippet": "Artículo 186. Todo trabajador que hubiere prestado servicios..."
    }
  ],
  "trace": {
    "intent": "domainSearch",
    "top_k": 4,
    "vector_db": "chroma",
    "llm_provider": "gemini"
  },
  "workflow_trace": {
    "conversation_id": "sesion-123",
    "total_steps": 4,
    "nodes_visited": ["classifier_node", "rag_node", "domain_search_node", "validate_node"],
    "tools_invoked": ["list_laws_by_topic", "get_article_text", "verify_citation_exists"],
    "tool_traces": [...],
    "validation_passed": true,
    "validation_details": {
      "citations_verified": 2,
      "vigency_checked": true,
      "reason": "Todas las citaciones verificadas correctamente en la base vectorial."
    },
    "execution_time_ms": 3421.5
  }
}
```

---

## 8. Interfaz de usuario (Chat UI)

La interfaz de usuario es una aplicación React con TypeScript construida con Vite. Provee un chat conversacional con soporte para visualización de citas y panel de rastreo de herramientas.

### 8.1 Pantalla principal del chat

La siguiente imagen muestra la interfaz principal del asistente con una conversación activa:

![Chat UI — Pantalla principal](examples/chat-ui-1.png)

*Figura 1: Interfaz principal del asistente de derecho laboral colombiano con respuesta generada por el sistema RAG. Se observa la burbuja de respuesta con texto en español fundamentado en el corpus legal.*

### 8.2 Panel de citas y trazabilidad

El sistema expone las citas de las fuentes recuperadas directamente en la interfaz:

![Chat UI — Panel de citas y fuentes](examples/chat-ui-2-citations.png)

*Figura 2: Panel lateral de citas mostrando los fragmentos del Código Sustantivo del Trabajo recuperados por el nodo `rag_node`. Cada cita incluye el documento fuente, el número de página y el fragmento textual relevante.*

### 8.3 Características de la UI

| Característica | Implementación |
|---------------|---------------|
| Burbujas de mensaje | Componente `message-bubble.tsx` |
| Panel de citas | Componente `citations-panel.tsx` |
| Header | Componente `header.tsx` |
| Snackbar de estado | Componente `app-snackbar.tsx` |
| Tema y estilos | Tailwind CSS + MUI Theme (`muiTheme.ts`) |
| Persistencia de sesión | `localStorage` con `conversation_id` |
| Comunicación con API | `chatService.ts` usando `fetch` |

---

## 9. Casos de uso documentados

A continuación se documentan 12 casos de uso que demuestran las funcionalidades del sistema.

---

### CU-01 — Consulta de días de vacaciones

**Intención detectada:** `domainSearch`  
**Descripción:** El usuario pregunta cuántos días de vacaciones corresponden a un trabajador en Colombia.

**Entrada:**
```
¿Cuántos días de vacaciones tiene un trabajador en Colombia?
```

**Flujo ejecutado:**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera contexto de ChromaDB (5 documentos)
3. `domain_search_node` (ReAct) → usa `list_laws_by_topic("vacaciones")` y `get_article_text("186", "CST")`
4. `validate_node` (ReAct) → usa `verify_citation_exists("CST", "186")` y `check_law_vigency("CST")`

**Respuesta esperada (extracto):**
> "Según el Artículo 186 del Código Sustantivo del Trabajo, todo trabajador que hubiere prestado servicios durante un año tiene derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas..."

**Herramientas usadas:** list_laws_by_topic, get_article_text, verify_citation_exists, check_law_vigency  
**Citas generadas:** 1–4 fragmentos del CST

---

### CU-02 — Resumen del Código Sustantivo del Trabajo

**Intención detectada:** `summarize`  
**Descripción:** El usuario solicita un resumen de los principales aspectos del CST.

**Entrada:**
```
Resume los puntos más importantes del Código Sustantivo del Trabajo colombiano
```

**Flujo ejecutado:**
1. `classifier_node` → `summarize`
2. `rag_node` → recupera contexto amplio (8–10 documentos)
3. `summarize_node` (ReAct) → usa `list_laws_by_topic("trabajo laboral")` y múltiples `get_article_text()` para capítulos principales
4. `validate_node` (ReAct) → verifica citaciones principales

**Respuesta esperada (formato):**
```
Resumen del Código Sustantivo del Trabajo colombiano:

• CONTRATO DE TRABAJO: Definición, tipos (término fijo, indefinido, obra o labor)...
• JORNADA LABORAL: Máximo 8 horas diarias / 48 semanales...
• SALARIO MÍNIMO: Reajuste anual según decreto gubernamental...
• VACACIONES: 15 días hábiles por año de servicio...
• CESANTÍAS: Un mes de salario por año de trabajo...
```

**Herramientas usadas:** list_laws_by_topic, get_article_text, get_document_metadata, verify_citation_exists

---

### CU-03 — Comparación entre contrato a término fijo e indefinido

**Intención detectada:** `compare`  
**Descripción:** El usuario solicita una comparación estructurada entre dos tipos de contratos.

**Entrada:**
```
¿Cuál es la diferencia entre un contrato a término fijo y uno a término indefinido en Colombia?
```

**Flujo ejecutado:**
1. `classifier_node` → `compare`
2. `rag_node` → recupera contexto sobre ambos tipos de contrato
3. `compare_node` (ReAct) → usa `search_by_law_number("CST")` y `get_article_text()` para término fijo e indefinido
4. `validate_node` (ReAct) → verifica citaciones

**Respuesta esperada (estructura):**
```
1. Definición de los conceptos
   - Contrato a término fijo: Duración preestablecida...
   - Contrato a término indefinido: Sin fecha de terminación...

2. Diferencias clave
   - Duración, preaviso de terminación, renovación automática...

3. Implicaciones legales
   - Para el empleado: estabilidad vs. flexibilidad...
   - Para el empleador: obligaciones de preaviso...
```

**Herramientas usadas:** list_laws_by_topic, search_by_law_number, get_article_text, verify_citation_exists

---

### CU-04 — Consulta general fuera del dominio laboral

**Intención detectada:** `generalSearch`  
**Descripción:** El usuario hace una pregunta de conocimiento general no relacionada con el derecho laboral.

**Entrada:**
```
¿Cuál es la capital de Francia?
```

**Flujo ejecutado:**
1. `classifier_node` → `generalSearch`
2. `general_search_node` → responde directamente con Groq (sin RAG)
3. `validate_node` → validación básica (sin tools)

**Respuesta esperada:**
> "La capital de Francia es París. **Nota:** Soy un asistente especializado en derecho laboral colombiano..."

**Herramientas usadas:** Ninguna (Groq LLM directo)  
**Sin recuperación RAG, sin citaciones**

---

### CU-05 — Consulta sobre liquidación de cesantías

**Intención detectada:** `domainSearch`  
**Descripción:** El usuario consulta cómo se calculan las cesantías.

**Entrada:**
```
¿Cómo se calculan las cesantías en Colombia y cuándo deben pagarse?
```

**Flujo ejecutado:**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera contexto relevante
3. `domain_search_node` (ReAct) → usa `get_article_text("249", "CST")` y herramientas adicionales
4. `validate_node` (ReAct) → verifica citaciones

**Respuesta esperada (extracto):**
> "Según el Artículo 249 del CST, el empleador debe pagar al trabajador un mes de salario por cada año de servicios y proporcionalmente por fracciones de año. La fórmula es: Cesantías = (Salario mensual × días trabajados) / 360..."

---

### CU-06 — Consulta sobre prima de servicios

**Intención detectada:** `domainSearch`  
**Descripción:** El usuario pregunta sobre la prima legal de servicios.

**Entrada:**
```
¿Qué es la prima de servicios y cuánto me corresponde?
```

**Flujo ejecutado:**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera Art. 306 CST
3. `domain_search_node` (ReAct) → usa `get_article_text("306", "CST")`
4. `validate_node` (ReAct) → verifica citación

**Respuesta esperada (extracto):**
> "La prima de servicios está regulada en el Artículo 306 del CST. Corresponde a 15 días de salario por semestre trabajado, pagaderos en junio y diciembre..."

---

### CU-07 — Acceso directo a un documento legal (Tool 3)

**Intención detectada:** `domainSearch` con recuperación por `doc_id`  
**Descripción:** El usuario solicita información detallada de un artículo específico. El sistema invoca `read_document` para recuperar el texto completo del documento.

**Entrada:**
```
Dame el texto completo del artículo sobre contratos de aprendizaje
```

**Flujo ejecutado:**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera fragmentos relevantes
3. `domain_search_node` (ReAct) → usa `get_article_text()` y `get_document_metadata()` para texto completo
4. `validate_node` (ReAct) → verifica citaciones

**Herramientas usadas:** get_article_text, get_document_metadata, verify_citation_exists

---

### CU-08 — Consulta sobre jornada laboral nocturna

**Intención detectada:** `domainSearch`  
**Descripción:** El usuario consulta sobre los recargos por trabajo nocturno.

**Entrada:**
```
¿Qué recargo corresponde por trabajar en horario nocturno en Colombia?
```

**Flujo ejecutado:**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera artículos sobre jornada y recargos
3. `domain_search_node` (ReAct) → usa `get_article_text("168", "CST")`
4. `validate_node` (ReAct) → verifica citación

**Respuesta esperada (extracto):**
> "Según el Artículo 168 del CST, el trabajo nocturno (entre las 9 p.m. y las 6 a.m.) tiene un recargo del 35% sobre el valor de la hora ordinaria..."

---

### CU-09 — Resumen de normas sobre despido sin justa causa

**Intención detectada:** `summarize`  
**Descripción:** El usuario pide un resumen de las normas sobre despido injustificado.

**Entrada:**
```
Resume la normativa colombiana sobre el despido sin justa causa
```

**Flujo ejecutado:**
1. `classifier_node` → `summarize`
2. `rag_node` → recupera múltiples artículos sobre despido
3. `summarize_node` (ReAct) → usa `list_laws_by_topic("despido")` y múltiples `get_article_text()`
4. `validate_node` (ReAct) → verifica citaciones

---

### CU-10 — Comparación entre salario integral y salario ordinario

**Intención detectada:** `compare`  
**Descripción:** El usuario quiere comparar los tipos de salario.

**Entrada:**
```
¿En qué se diferencia el salario integral del ordinario en Colombia?
```

**Flujo ejecutado:**
1. `classifier_node` → `compare`
2. `rag_node` → recupera artículos sobre salario integral (Art. 132 CST)
3. `compare_node` (ReAct) → usa `search_by_law_number("CST")` y `get_article_text("132")`
4. `validate_node` (ReAct) → verifica citaciones

**Respuesta esperada (extracto sección 2):**
> "Diferencias clave:
> - El salario integral incluye prestaciones sociales en su valor; el ordinario no.
> - El salario integral requiere ser al menos 10 SMLMV..."

---

### CU-11 — Manejo de pregunta con resultado de validación fallida (reintento)

**Intención detectada:** `domainSearch`  
**Descripción:** La primera respuesta generada no supera el umbral de validación. El grafo activa el reintento automático desde `rag_node`.

**Entrada:**
```
¿Qué dice la ley sobre el acoso laboral?
```

**Flujo ejecutado (con reintento):**
1. `classifier_node` → `domainSearch`
2. `rag_node` → recupera contexto
3. `domain_search_node` (ReAct) → genera primera respuesta
4. `validate_node` → `is_valid=False` (respuesta insuficiente)
5. **Reintento:** vuelve a `domain_search_node` con instrucciones mejoradas
6. `validate_node` → `is_valid=True` en segundo intento
7. Respuesta final entregada al usuario

**Registro de consola esperado:**
```
[GRAPH] validate_route - Invalid answer, retrying RAG node
[GRAPH] rag_node - Executing RAG pipeline...
[GRAPH] validate_route - Answer is VALID, ending
```

---

### CU-12 — Consulta en cadena (memoria conversacional)

**Intención:** Múltiples turnos con `conversation_id` compartido  
**Descripción:** El usuario hace varias preguntas relacionadas en la misma sesión. El historial de mensajes se mantiene por `InMemorySaver`.

**Turno 1:**
```
¿Qué es el contrato de trabajo?
```
**Turno 2:**
```
¿Y cuáles son sus elementos esenciales?
```
**Turno 3:**
```
¿Cuándo se puede terminar?
```

Cada turno hereda el contexto del anterior. El `thread_id` de LangGraph garantiza que el estado del grafo persista entre invocaciones dentro de la misma `conversation_id`.

---

## 10. Registros de ejecución

A continuación se documentan los registros de consola característicos de cada fase del sistema durante la ejecución.

### 10.1 Arranque del servidor

```
✅ groq_LLM ready: llama-3.1-8b-instant
✅ gemini_LLM ready: gemini-2.5-flash
✅ ReAct agents created: domain_search, summarize, compare, validate

======================================================================
✅ 7 TOOLS REGISTERED SUCCESSFULLY
======================================================================
1. list_laws_by_topic - List laws by topic (ChromaDB)
2. search_by_law_number - Search by law identifier (ChromaDB)
3. get_article_text - Get specific article text (ChromaDB + regex)
4. get_document_metadata - Get document metadata (ChromaDB)
5. find_related_jurisprudence - Find related case law (ChromaDB)
6. verify_citation_exists - Anti-hallucination verification (ChromaDB)
7. check_law_vigency - Law vigency check (Reference DB)
======================================================================

======================================================================
✅ LANGGRAPH COMPILED SUCCESSFULLY
======================================================================
Graph Structure:
  START → classifier_node
    ├→ domainSearch/summarize/compare → rag_node → expert_node (ReAct)
    └→ generalSearch → general_search_node (Groq)
  → validate_node (ReAct) → [END | retry]
======================================================================
```

### 10.2 Ejecución de consulta `domainSearch`

```
======================================================================
[CHAT] Starting workflow for: ¿Cuántos días de vacaciones tiene un t...
======================================================================

[DEBUG]: classifier_node - intent=domainSearch

[DEBUG]: rag_node - Solo retrieval (no genera)
[DEBUG]: rag_node - Recuperados 5 documentos

[DEBUG]: domain_search_node (ReAct con contexto)
[TOOL 3] list_laws_by_topic - Tema: vacaciones
[TOOL 3] list_laws_by_topic - Leyes encontradas: 2
[TOOL 2] get_article_text - Art. 186 de Código Sustantivo del Trabajo
[TOOL 2] get_article_text - Encontrado: True (3 chunks)
[DEBUG]: domain_search_node - Tools adicionales: 2 llamadas

[DEBUG]: validate_node (ReAct) - intent=domainSearch
[TOOL 7] verify_citation_exists - CST, Art. 186
[TOOL 7] verify_citation_exists - VERIFICADA
[TOOL 5] check_law_vigency - Consultando: Código Sustantivo del Trabajo
[TOOL 5] check_law_vigency - Vigente: True

======================================================================
[CHAT] Workflow complete
  Intent: domainSearch
  Tools Used: list_laws_by_topic, get_article_text, verify_citation_exists, check_law_vigency
  Citations: 4
  Valid: True
======================================================================
```

### 10.3 Ejecución de consulta `generalSearch`

```
[DEBUG]: classifier_node - intent=generalSearch
[DEBUG]: general_search_node (Groq) - Response ready
[DEBUG]: validate_node (ReAct) - intent=generalSearch
[DEBUG]: validate_node - Validación básica (sin tools)
[CHAT] Workflow complete - No citations (generalSearch)
```

### 10.4 Ejecución con reintento por validación fallida

```
[NODE] validate_node - Valid: False, reason: Citación Art. 999 no verificada
[GRAPH] validate_route - Invalid answer, retrying expert node

[NODE] domain_search_node (ReAct) - Reintento con contexto mejorado
[TOOL] get_article_text - Art. 186 CST retrieved
[TOOL] verify_citation_exists - Art. 186 CST: True
[NODE] validate_node - Valid: True
[GRAPH] validate_route - Answer is VALID, ending
```

### 10.5 Respuesta del endpoint `/health`

```http
GET /health HTTP/1.1
→ 200 OK
{"ok": true}
```

---

## 11. Conclusiones

### 11.1 Fortalezas del sistema

1. **Arquitectura ReAct autónoma:** Cada nodo experto (domain_search, summarize, compare, validate) es un agente ReAct que decide autónomamente qué herramientas usar, eliminando lógica pre-cableada y permitiendo adaptabilidad.

2. **Principio de Least Privilege:** Cada nodo solo tiene acceso a las herramientas que necesita (4, 3, 3, 2 respectivamente), reduciendo superficie de error y mejorando seguridad.

3. **Trazabilidad completa:** Cada respuesta viene acompañada de citas con documento fuente, página y fragmento, garantizando que el usuario pueda verificar la información en la norma original.

4. **Validación anti-alucinación:** El `validate_node` usa `verify_citation_exists` y `check_law_vigency` para verificar que las citaciones legales realmente existen y están vigentes.

5. **Selección estratégica de LLMs:** Gemini 2.5 Flash para agentes ReAct (razonamiento complejo); Groq llama-3.1-8b-instant para consultas generales y determinación de top_k.

6. **Embeddings consistentes:** Google `gemini-embedding-001` garantiza alineación semántica con el LLM principal.

7. **Historial conversacional:** `_build_conversation_history()` inyecta los últimos 5 turnos en cada agente, permitiendo respuestas contextuales.

### 11.2 Limitaciones actuales

- La memoria conversacional (`InMemorySaver`) no persiste entre reinicios del servidor.
- El corpus se limita a los documentos indexados en `db_chroma`; documentos fuera del índice no pueden ser recuperados.
- El reintento máximo está limitado a 1 para evitar bucles infinitos y latencia excesiva.
- La base de vigencia de leyes (`LAW_VIGENCY_DB`) es estática y requiere actualización manual.

### 11.3 Propuestas de mejora futuras

- Implementar persistencia de memoria con `PostgresSaver` o `SqliteSaver` de LangGraph.
- Agregar endpoint `POST /ingest` para ingesta dinámica de nuevos documentos legales.
- Conectar `check_law_vigency` a SUIN-Juriscol para verificación de vigencia en tiempo real.
- Agregar autenticación JWT para entornos de producción.
- Expandir el corpus con jurisprudencia de la Corte Suprema de Justicia y el Consejo de Estado.
- Implementar streaming de respuestas para mejor UX.

---

*Informe generado para el proyecto SPE AI Labor Law Assistant — Universidad Nacional de Colombia*