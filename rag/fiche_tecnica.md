# FICHA TÉCNICA - SPE AI Labor Law Assistant
## Asistente Inteligente de Derecho Laboral Colombiano

**Versión:** 2.0.0  
**Fecha de Actualización:** 28 de febrero de 2026  
**Estado:** Production-Ready  

---

## 1. DESCRIPCIÓN EJECUTIVA

El **SPE AI Labor Law Assistant** es una aplicación web inteligente que proporciona asesoramiento sobre derecho laboral colombiano mediante un asistente conversacional basado en IA. El sistema integra:

- **Retrieval-Augmented Generation (RAG)** con arquitectura de agentes ReAct
- **LangGraph StateGraph** para orquestación de flujos multi-agente
- **Clasificación de intención** automática con 4 flujos especializados
- **Visualización interactiva de trazabilidad** de fragmentos recuperados
- **Panel de citas legales** con referencias documentales precisas
- **Historial conversacional** persistente por sesión
- **Arquitectura modular** con separación frontend/backend

El asistente puede responder preguntas sobre contratos laborales, derechos de trabajadores, cesantías, vacaciones y terminación de contratos, basándose en el **Código Sustantivo del Trabajo (CST)** y normatividad laboral colombiana.

---

## 2. OBJETIVOS DEL PROYECTO

### Objetivo General
Desarrollar un asistente inteligente que proporcione respuestas precisas y verificables sobre derecho laboral colombiano, mostrando las fuentes legales utilizadas en cada respuesta.

### Objetivos Específicos
1. **Clasificación inteligente**: Detectar automáticamente el tipo de consulta (búsqueda, resumen, comparación, general)
2. **Recuperación de contexto legal**: Implementar RAG híbrido con ChromaDB + tools especializados
3. **Agentes autónomos**: Usar patrón ReAct para que cada agente decida qué herramientas necesita
4. **Trazabilidad completa**: Mostrar qué fragmentos se utilizaron para generar cada respuesta
5. **Validación de citas**: Verificar que las citaciones legales existan y estén vigentes
6. **Historial conversacional**: Mantener contexto entre mensajes del mismo usuario

---

## 3. STACK TECNOLÓGICO

### 3.1 Backend (Python)
| Tecnología | Versión | Propósito |
|------------|---------|----------|
| **FastAPI** | 0.100+ | Framework web asincrónico para APIs RESTful de alto rendimiento |
| **Pydantic** | 2.0+ | Validación de datos y serialización JSON con type hints |
| **LangGraph** | 0.2+ | Orquestación de flujos multi-agente con StateGraph |
| **LangChain** | 0.3+ | Framework para agentes ReAct y gestión de LLMs |
| **ChromaDB** | 0.4+ | Base de datos vectorial para embeddings de textos legales |
| **Gemini 2.5 Flash** | - | LLM principal para clasificación y generación (Google AI) |
| **Groq Llama 3.1** | 8B | LLM económico para consultas generales |
| **Google Embeddings** | embedding-001 | Modelo de embeddings para búsqueda semántica |

### 3.2 Frontend (React/TypeScript)
| Tecnología | Versión | Propósito |
|------------|---------|----------|
| **React** | 18+ | Framework UI para componentes interactivos |
| **TypeScript** | 5.0+ | Type safety en JavaScript para evitar errores en tiempo de compilación |
| **Vite** | 6.3.5 | Build tool ultrarrápido para desarrollo con HMR |
| **Material-UI (MUI)** | 7.3.5 | Componentes UI profesionales y accesibles |
| **CSS Modular** | - | Estilos personalizados para trazabilidad y visualización |

### 3.3 Infraestructura & DevOps
| Componente | Especificación |
|-----------|----------------|
| **OS** | Windows / Linux (desarrollo) |
| **Python Env** | Virtual environment con pip |
| **Node/npm** | Gestor de dependencias frontend |
| **Build** | Vite + TypeScript compiler |
| **API Communication** | HTTP REST con JSON |
| **Database** | ChromaDB (vectorial local) |
| **Memory** | InMemorySaver (historial conversacional) |

---

## 4. ARQUITECTURA DEL SISTEMA

### 4.1 Diagrama de Flujo LangGraph

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH STATEGRAPH                            │
│                                                                      │
│   ┌─────────────┐                                                   │
│   │   START     │                                                   │
│   └──────┬──────┘                                                   │
│          │                                                          │
│          ▼                                                          │
│   ┌─────────────────┐                                               │
│   │ classifier_node │  (Gemini 2.5 Flash)                           │
│   │   Detecta:      │                                               │
│   │   - domainSearch│                                               │
│   │   - summarize   │                                               │
│   │   - compare     │                                               │
│   │   - generalSearch│                                              │
│   └────────┬────────┘                                               │
│            │                                                        │
│     ┌──────┴──────────────────────────────┐                         │
│     │ classify_route                      │                         │
│     ▼                                     ▼                         │
│  ┌──────────────┐                   ┌──────────────────┐            │
│  │   rag_node   │                   │ general_search   │            │
│  │ (retrieval)  │                   │ (Groq Llama 3.1) │            │
│  └──────┬───────┘                   └────────┬─────────┘            │
│         │                                    │                       │
│    rag_route                                 │                       │
│    ┌────┼────┐                               │                       │
│    ▼    ▼    ▼                               │                       │
│ ┌─────┐┌─────┐┌─────┐                        │                       │
│ │dom. ││sum. ││comp.│ (ReAct Agents)        │                       │
│ │search││node ││node │ con Tools            │                       │
│ └──┬──┘└──┬──┘└──┬──┘                        │                       │
│    │      │      │                           │                       │
│    └──────┴──────┴───────────────────────────┘                       │
│                    │                                                 │
│                    ▼                                                 │
│            ┌──────────────┐                                         │
│            │ validate_node│ (ReAct con verify tools)                │
│            └──────┬───────┘                                         │
│                   │                                                  │
│            validate_route                                            │
│            ┌──────┴──────┐                                          │
│            ▼             ▼                                          │
│         ┌─────┐     ┌────────┐                                      │
│         │ END │     │rag_node│ (retry si inválido)                  │
│         └─────┘     └────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 RAG Retrieval → Expert Generation

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLUJO OPTIMIZADO (1 retrieval + 1 generación)                     │
│                                                                      │
│  1. classifier_node → Detecta intent                                │
│                                                                      │
│  2. rag_node        → SOLO RETRIEVAL (no genera)                    │
│                        - Busca en ChromaDB                          │
│                        - Retorna contexto_legal + citaciones        │
│                                                                      │
│  3. expert_node     → GENERA con contexto                           │
│     (ReAct Agent)      - Recibe contexto del rag_node              │
│                        - Decide si necesita tools adicionales       │
│                        - Genera respuesta final                     │
│                                                                      │
│  4. validate_node   → Verifica citaciones                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- Una sola consulta a ChromaDB (no redundante)
- Una sola generación LLM por consulta
- El agente experto puede usar tools si necesita más detalle
- Menor latencia y costo

### 4.3 GraphState (Estado Compartido)

```python
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # Historial
    question: str                    # Pregunta actual
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
    contexto_legal: str              # Contexto recuperado de ChromaDB
    documentos_recuperados: list     # Citaciones para el response
    is_valid: bool                   # Resultado de validación
```

---

## 5. COMPONENTES PRINCIPALES

### 5.1 Frontend Components

#### **App.tsx** - Contenedor Principal
- Gestiona el estado global del chat
- Maneja envío/recepción de mensajes
- Controla la visibilidad de paneles

```typescript
// Maneja respuestas del backend con estructura completa
const response = await sendMessage(userMessage);
if (typeof response === "object") {
  // Nueva estructura con citations y traces
  addMessage({
    text: response.answer,
    citations: response.citations,
    trace: response.trace,
    workflow_trace: response.workflow_trace
  });
}
```

#### **CitationsPanel.tsx** - Panel de Citas Legales
**Propósito**: Mostrar fuentes legales de forma legible y profesional

**Características**:
- Panel expandible/colapsible
- Agrupa citas por documento fuente
- Muestra número de página
- Fragmento del texto entrecomillado
- Colores diferenciados para cada sección

```typescript
interface Citation {
  source: string;      // "DECRETO 1072 DE 2015"
  page?: number;       // 200
  snippet: string;     // Fragmento del texto
  url?: string;        // URL del documento (opcional)
}
```

**Estilos**: Definidos en `traceability.css`
- Fondo degradado (f9f5ff → f5faff)
- Bordes redondeados y sombreado suave
- Tipografía profesional con pesos variables

#### **WorkflowTracePanel.tsx** - Panel de Trazabilidad
**Propósito**: Mostrar el proceso de ejecución y métricas

**Características**:
- Timeline de herramientas ejecutadas
- Duración de cada paso
- Estado de validación (success/warning/error)
- Métricas de rendimiento
- Chips de metadata (relevancia, confianza)

```typescript
interface WorkflowTrace {
  total_duration_ms: number;
  tools_used: ToolTraceStep[];
  validation_metrics: ValidationDetails;
}

interface ToolTraceStep {
  tool_name: string;
  status: 'success' | 'warning' | 'error';
  duration_ms: number;
  input_tokens?: number;
  output_tokens?: number;
}
```

#### **MessageBubble.tsx** - Burbuja de Mensaje
- Renderiza mensaje de usuario o asistente
- Integra CitationsPanel cuando hay citas
- Integra WorkflowTracePanel cuando hay trace
- Indicador de escritura (typing dots)

### 5.2 Backend Services

#### **main.py** - Punto de Entrada
- Inicialización de FastAPI
- Configuración CORS
- Registro de rutas

#### **api/routes.py** - Endpoints
```python
@app.post("/chat")
def chat(body: ChatRequest) -> ChatResponse:
    """
    Procesa pregunta y retorna respuesta con trazabilidad completa
    
    Request:
    {
        "question": "¿Qué dice el artículo 62 del CST?",
        "conversation_id": "user123"  # Opcional, para historial
    }
    
    Response:
    {
        "ok": true,
        "request_id": "req-abc123-user123",
        "answer": "El artículo 62 del CST establece...",
        "citations": [
            {"source": "CST", "page": 10, "chunk_id": "chunk_42", "snippet": "..."}
        ],
        "trace": {
            "intent": "domainSearch",
            "top_k": 8,
            "vector_db": "chroma",
            "llm_provider": "gemini"
        }
    }
    """
```

#### **rag/agents.py** - Orquestación LangGraph
Implementa el grafo de agentes con LangGraph StateGraph:

**Nodos del Grafo:**

| Nodo | LLM | Función |
|------|-----|---------|
| `classifier_node` | Gemini 2.5 Flash | Detecta intent (domainSearch/summarize/compare/generalSearch) |
| `rag_node` | - | Solo retrieval de ChromaDB, no genera |
| `domain_search_node` | Gemini (ReAct) | Búsqueda legal específica con tools |
| `summarize_node` | Gemini (ReAct) | Genera resúmenes estructurados |
| `compare_node` | Gemini (ReAct) | Compara conceptos legales |
| `general_search_node` | Groq Llama 3.1 | Respuestas generales (sin RAG) |
| `validate_node` | Gemini (ReAct) | Verifica citaciones con tools |

**Agentes ReAct (create_agent):**
```python
# Cada agente decide autónomamente qué tools usar
domain_search_agent = create_agent(
    model=gemini_LLM,
    tools=DOMAIN_SEARCH_TOOLS,
    system_prompt=DOMAIN_SEARCH_PROMPT,
    name="domain_search_agent"
)
```

**Historial Conversacional:**
```python
memory = InMemorySaver()
chat = graph.compile(checkpointer=memory)

# El historial se mantiene por conversation_id
config = {"configurable": {"thread_id": conversation_id}}
```

#### **rag/retriever.py** - Búsqueda Vectorial
- `recuperar_contexto_dinamico()`: Búsqueda semántica en ChromaDB
- `formatear_documentos_para_gemini()`: Formatea chunks para el LLM
- Extracción de metadata (source, page, chunk_id)

#### **rag/prompts.py** - Prompts del Sistema
Contiene todos los prompts centralizados:
- `CLASSIFIER_PROMPT`: Clasificación de intención
- `GENERAL_SYSTEM_PROMPT`: Respuestas generales
- `DOMAIN_SEARCH_PROMPT`: Instrucciones para búsqueda legal
- `SUMMARIZE_PROMPT`: Instrucciones para resúmenes
- `COMPARE_PROMPT`: Instrucciones para comparaciones
- `VALIDATE_PROMPT`: Instrucciones para validación

#### **db/chroma.py** - Capa de Vectores
- Inicialización de ChromaDB con Google embeddings
- Persistencia local en `./db_chroma`
- Búsqueda por similitud semántica

#### **rag/tools.py** - Herramientas para Agentes ReAct

Implementa 7 tools organizadas por función (Principle: Least Privilege):

**Data Access Tools (para búsqueda):**

| Tool | Descripción | Uso |
|------|-------------|-----|
| `list_laws_by_topic` | Lista leyes relacionadas con un tema | domain_search, summarize, compare |
| `search_by_law_number` | Busca contenido por número de ley | domain_search, compare |
| `get_article_text` | Obtiene texto de un artículo específico | domain_search, summarize, compare |
| `get_document_metadata` | Retorna metadata de un documento | summarize |
| `find_related_jurisprudence` | Busca jurisprudencia relacionada | domain_search |

**Validation Tools (para validación):**

| Tool | Descripción | Uso |
|------|-------------|-----|
| `verify_citation_exists` | Verifica que una citación exista en la BD | validate |
| `check_law_vigency` | Verifica si una ley está vigente | validate |

**Tool Sets por Nodo:**
```python
DOMAIN_SEARCH_TOOLS = [list_laws_by_topic, search_by_law_number, 
                       get_article_text, find_related_jurisprudence]
SUMMARIZE_TOOLS = [list_laws_by_topic, get_article_text, get_document_metadata]
COMPARE_TOOLS = [list_laws_by_topic, search_by_law_number, get_article_text]
VALIDATE_TOOLS = [verify_citation_exists, check_law_vigency]
```

---

## 6. TIPOS Y ESTRUCTURAS DE DATOS

### 6.1 Types Frontend (chat-ui/src/app/types.ts)

```typescript
// Mensaje en la conversación
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'typing' | 'error';
  text: string;
  ts: string;  // timestamp ISO
  citations?: Citation[];
  trace?: Trace;
  workflow_trace?: WorkflowTrace;
}

// Cita de fuente legal
interface Citation {
  source: string;      // ej: "DECRETO 1072 DE 2015"
  page?: number;
  snippet: string;
  url?: string;
}

// Trazabilidad de recuperación
interface Trace {
  query: string;
  retrieved_documents: {
    source: string;
    page: number;
    relevance_score: number;
  }[];
  retrieval_duration_ms: number;
}

// Trazabilidad de workflow (tools)
interface WorkflowTrace {
  total_duration_ms: number;
  tools_used: ToolTraceStep[];
  validation_metrics: ValidationDetails;
}

interface ToolTraceStep {
  tool_name: string;
  status: 'success' | 'warning' | 'error';
  duration_ms: number;
  input?: string;
  output?: string;
}

interface ValidationDetails {
  source_validation_passed: boolean;
  consistency_score: number;  // 0-100
  confidence_level: 'high' | 'medium' | 'low';
}
```

### 6.2 API Schemas (api/schemas.py)

```python
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    chunk_id: str
    snippet: str

class Trace(BaseModel):
    intent: str                    # domainSearch, summarize, compare, generalSearch
    top_k: int                     # Número de documentos recuperados
    vector_db: str = "chroma"
    llm_provider: str = "gemini"

class ChatResponse(BaseModel):
    ok: bool
    request_id: str
    answer: str
    citations: List[Citation]
    trace: Trace
    workflow_trace: Optional[Dict] = None
    metadata: Optional[Dict] = None
```

---

## 7. HERRAMIENTAS IMPLEMENTADAS (Tools)

### 7.1 list_laws_by_topic ✓

**¿Por qué es útil?**
- Identifica qué leyes/decretos están relacionados con un tema
- Permite al agente saber dónde buscar antes de profundizar
- Mejora la estrategia de búsqueda

**Implementación**:
```python
@tool
def list_laws_by_topic(topic: str) -> str:
    """
    Lista las leyes y decretos relacionados con un tema específico.
    
    Input: "vacaciones"
    Output: "Leyes relacionadas con 'vacaciones':
            - Código Sustantivo del Trabajo (Arts. 186-192)
            - Decreto 1072 de 2015 (Capítulo 5)"
    """
```

### 7.2 search_by_law_number ✓

**¿Por qué es útil?**
- Búsqueda precisa cuando el usuario menciona una ley específica
- Evita ruido de búsqueda semántica general

**Implementación**:
```python
@tool
def search_by_law_number(law_number: str) -> str:
    """
    Busca contenido relacionado con un número de ley específico.
    
    Input: "Ley 100 de 1993"
    Output: Fragmentos relevantes de esa ley
    """
```

### 7.3 get_article_text ✓

**¿Por qué es útil?**
- Obtiene el texto exacto de un artículo específico
- Máxima precisión para consultas específicas

**Implementación**:
```python
@tool
def get_article_text(article_number: str, law_name: str) -> str:
    """
    Obtiene el texto completo de un artículo específico.
    
    Input: article_number="62", law_name="CST"
    Output: "ARTÍCULO 62. TERMINACIÓN DEL CONTRATO POR JUSTA CAUSA..."
    """
```

### 7.4 find_related_jurisprudence ✓

**¿Por qué es útil?**
- Complementa la normativa con decisiones judiciales
- Proporciona interpretación aplicada de las leyes

**Implementación**:
```python
@tool
def find_related_jurisprudence(legal_topic: str) -> str:
    """
    Busca jurisprudencia relacionada con un tema legal.
    
    Input: "despido sin justa causa"
    Output: Sentencias relevantes de la Corte Suprema/Constitucional
    """
```

### 7.5 verify_citation_exists ✓

**¿Por qué es útil?**
- Previene alucinaciones verificando que la cita existe
- Aumenta confiabilidad del asistente legal

**Implementación**:
```python
@tool
def verify_citation_exists(article: str, law: str) -> str:
    """
    Verifica si una citación legal existe en la base de datos.
    
    Input: article="62", law="CST"
    Output: "✓ Citación verificada: Artículo 62 del CST existe en la base de datos"
    """
```

### 7.6 check_law_vigency ✓

**¿Por qué es útil?**
- Verifica que las leyes citadas estén vigentes
- Advierte sobre leyes derogadas o modificadas

**Implementación**:
```python
@tool
def check_law_vigency(law_name: str) -> str:
    """
    Verifica si una ley está vigente o ha sido modificada.
    
    Input: "Código Sustantivo del Trabajo"
    Output: "✓ El CST está vigente con modificaciones. 
             Última actualización: Ley 2101 de 2021"
    """
```

---

## 8. ESTRUCTURA DEL PROYECTO

```
spe-ai-labor-law-assistant/
│
├── chat-ui/                          # Frontend React/Vite
│   ├── src/
│   │   ├── main.tsx                 # Punto de entrada
│   │   ├── app/
│   │   │   ├── App.tsx              # Componente principal
│   │   │   ├── types.ts             # Interfaces TypeScript
│   │   │   └── components/
│   │   │       ├── ui/
│   │   │       │   ├── message-bubble.tsx        # Burbuja de mensaje
│   │   │       │   ├── citations-panel.tsx       # Panel de citas legales
│   │   │       │   └── [otros componentes UI]
│   │   │       └── figma/
│   │   ├── services/
│   │   │   └── chatService.ts       # Cliente HTTP para backend
│   │   └── styles/
│   │       ├── colors.ts            # Paleta de colores
│   │       ├── traceability.css     # Estilos de paneles
│   │       └── theme.css
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── rag/                              # Backend Python/FastAPI
│   ├── app/
│   │   ├── main.py                  # Aplicación FastAPI
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── routes.py            # Endpoints: /chat, /health
│   │   │   └── schemas.py           # Pydantic schemas (ChatRequest, ChatResponse)
│   │   ├── core/
│   │   │   └── config.py            # Settings (API keys, modelos)
│   │   ├── db/
│   │   │   └── chroma.py            # Interfaz ChromaDB
│   │   ├── rag/
│   │   │   ├── agents.py            # LangGraph StateGraph + ReAct agents
│   │   │   ├── retriever.py         # Búsqueda vectorial
│   │   │   ├── prompts.py           # Prompts centralizados
│   │   │   ├── tools.py             # 7 tools para agentes
│   │   │   ├── ingestion.py         # Procesamiento de PDFs
│   │   │   └── pipelines/
│   │   │       └── run_ingestion.py # Script de ingesta
│   │   └── data/
│   │       └── CODIGO SUSTANTIVO DEL TRABAJO.pdf
│   │
│   ├── db_chroma/                    # Base de datos vectorial (persistente)
│   │   ├── chroma.sqlite3
│   │   └── [colecciones de embeddings]
│   │
│   ├── storage/                      # Almacenamiento auxiliar
│   ├── tests/
│   │   ├── test_api.py
│   │   └── __init__.py
│   │
│   ├── pyproject.toml               # Dependencias Python
│   ├── Makefile                     # Comandos de desarrollo
│   ├── README.md
│   └── fiche_tecnica.md             # Este documento
│
└── README.md                         # Documentación principal
```

---

## 8. CONCLUSIÓN

El **SPE AI Labor Law Assistant** es una solución completa que demuestra cómo combinar:

- **IA Generativa Multi-Modelo** (Gemini 2.5 Flash + Groq Llama 3.1)
- **Orquestación de Agentes** (LangGraph StateGraph)
- **Patrón ReAct** para decisiones autónomas de herramientas
- **Búsqueda Vectorial** (ChromaDB con Google Embeddings)
- **Arquitectura Eficiente** (Opción C: 1 retrieval + 1 generación)
- **Frontend Moderno** (React + TypeScript)
- **Backend Robusto** (FastAPI)

Para crear un **asistente legal especializado** que proporciona respuestas verificables basadas en el **Código Sustantivo del Trabajo** colombiano.

**Características destacadas:**
- 📊 Clasificación automática de intención (4 flujos)
- 🔧 7 herramientas especializadas para agentes
- 💬 Historial conversacional por sesión
- ✅ Validación de citaciones legales
- 📚 Trazabilidad completa de fuentes

La arquitectura es modular, testeable y escalable, permitiendo agregar nuevas fuentes legales, mejorar prompts y ajustar las herramientas sin cambios mayores.
