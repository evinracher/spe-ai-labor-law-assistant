# FICHA TÉCNICA - SPE AI Labor Law Assistant
## Asistente Inteligente de Derecho Laboral Colombiano

**Versión:** 1.0.0  
**Fecha de Actualización:** 27 de febrero de 2026  
**Estado:** Production-Ready  

---

## 1. DESCRIPCIÓN EJECUTIVA

El **SPE AI Labor Law Assistant** es una aplicación web inteligente que proporciona asesoramiento sobre derecho laboral colombiano mediante un asistente conversacional basado en IA. El sistema integra:

- **Retrieval-Augmented Generation (RAG)** para consultar fuentes legales reales
- **Visualización interactiva de trazabilidad** de fragmentos recuperados
- **Panel de citas legales** con referencias documentales precisas
- **Arquitectura modular** con separación frontend/backend

El asistente puede responder preguntas sobre contratos laborales, derechos de trabajadores, normas de seguridad y salud ocupacional, basándose en decretos colombianos reales (DECRETO 1072 DE 2015, DECRETO 780 DE 2016, DECRETO 1833 DE 2016).

---

## 2. OBJETIVOS DEL PROYECTO

### Objetivo General
Desarrollar un asistente inteligente que proporcione respuestas precisas y verificables sobre derecho laboral colombiano, mostrando las fuentes legales utilizadas en cada respuesta.

### Objetivos Específicos
1. **Recuperación de contexto legal**: Implementar RAG para buscar fragmentos relevantes en la legislación colombiana
2. **Trazabilidad completa**: Mostrar qué fragmentos se utilizaron para generar cada respuesta
3. **Experiencia usuario mejorada**: Visualizar citas legales de forma legible y navegable
4. **Validación de respuestas**: Incluir métricas de calidad y confianza en las respuestas
5. **Escalabilidad**: Arquitectura preparada para agregar más fuentes legales

---

## 3. STACK TECNOLÓGICO

### 3.1 Backend (Python)
| Tecnología | Versión | Propósito |
|------------|---------|----------|
| **FastAPI** | 0.100+ | Framework web asincrónico para APIs RESTful de alto rendimiento |
| **Pydantic** | 2.0+ | Validación de datos y serialización JSON con type hints |
| **Langchain** | 0.1+ | Orquestación de LLMs y cadenas de procesamiento RAG |
| **ChromaDB** | - | Base de datos vectorial para embeddings de textos legales |
| **OpenAI API** | - | Modelo GPT para generación de respuestas y embeddings |
| **PyPDF2/Pdfplumber** | - | Extracción de texto de PDFs de legislación |

### 3.2 Frontend (React/TypeScript)
| Tecnología | Versión | Propósito |
|------------|---------|----------|
| **React** | 18+ | Framework UI para componentes interactivos |
| **TypeScript** | 5.0+ | Type safety en JavaScript para evitar errores en tiempo de compilación |
| **Vite** | 6.3.5 | Build tool ultrarrápido para desarrollo con HMR |
| **Material-UI (MUI)** | 7.3.5 | Componentes UI profesionales y accesibles |
| **CSS Modular** | - | Estilos personalizados para trazabilidad y visualización |
| **React Router** | - | Navegación entre vistas (si aplica) |

### 3.3 Infraestructura & DevOps
| Componente | Especificación |
|-----------|----------------|
| **OS** | Linux (desarrollo) |
| **Python Env** | Virtual environment con pip |
| **Node/npm** | Gestor de dependencias frontend |
| **Build** | Vite + TypeScript compiler |
| **API Communication** | HTTP REST con JSON |
| **Database** | ChromaDB (vectorial local) |

---

## 4. ARQUITECTURA DEL SISTEMA

### 4.1 Diagrama General

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   Chat UI    │  │  Message     │  │  Traceability Panels     │   │
│  │ (App.tsx)    │  │  Bubble      │  │ ├─ CitationsPanel       │   │
│  │              │  │              │  │ ├─ WorkflowTracePanel   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘   │
│         │                 │                     │                    │
│         └─────────────────┼─────────────────────┘                    │
│                           │                                          │
│                    ┌──────▼──────┐                                   │
│                    │ chatService  │ (HTTP Client)                    │
│                    └──────┬───────┘                                  │
└─────────────────────────┬────────────────────────────────────────────┘
                          │
                    HTTP POST
                   /api/chat
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│                      BACKEND (Python/FastAPI)                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    RAG Pipeline                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │  │
│  │  │ Question │──▶ Embedding │──▶Retriever│──▶LLM Generation │ │  │
│  │  │ Parser   │  │ Service   │  │          │  │                │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬───────────┘ │  │
│  └───────────────────────────────────────────────┬──────────────┘  │
│                                                  │                  │
│  ┌──────────────────────────────────────────────▼──────────────┐   │
│  │  Response Builder                                           │   │
│  │  ├─ answer: str                                            │   │
│  │  ├─ citations: Citation[]   (source, page, snippet)       │   │
│  │  ├─ trace: Trace            (query, results, timestamps)  │   │
│  │  └─ workflow_trace: WorkflowTrace (tools, steps, metrics) │   │
│  └───────────────┬──────────────────────────────────────────┘    │
│                  │                                                 │
│  ┌──────────────▼──────────────┐  ┌──────────────────────────┐   │
│  │   ChromaDB Vector Store      │  │  PDF Documents Storage   │   │
│  │  ├─ DECRETO 1072 2015       │  │  (Decretos colombianos)  │   │
│  │  ├─ DECRETO 780 2016        │  │                          │   │
│  │  ├─ DECRETO 1833 2016       │  │                          │   │
│  │  └─ (embeddings + chunks)   │  └──────────────────────────┘   │
│  └────────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Flujo de Datos en una Consulta

```
1. Usuario escribe pregunta
   ↓
2. chatService.sendMessage(text) → Backend /api/chat
   ↓
3. RAG Pipeline:
   a. Procesar pregunta → embedding
   b. Buscar en ChromaDB → top-k fragmentos relevantes
   c. Extraer metadata (source, page, snippet)
   d. Construir contexto legal
   ↓
4. LLM Generation:
   a. Enviar prompt con contexto + pregunta a OpenAI
   b. Recibir respuesta generada
   c. Asociar fragmentos utilizados
   ↓
5. Response Building:
   {
     answer: "La respuesta generada...",
     citations: [
       { source: "DECRETO 1072 DE 2015", page: 200, snippet: "..." },
       ...
     ],
     trace: { query, retrieved_docs, timestamps },
     workflow_trace: { tools_used, execution_steps }
   }
   ↓
6. Frontend Rendering:
   a. Mostrar mensaje del asistente (answer)
   b. Expandir CitationsPanel con referencias legales
   c. Mostrar WorkflowTracePanel con métricas de ejecución
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
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Procesa pregunta y retorna respuesta con trazabilidad completa
    
    Request:
    {
        "message": "¿Cuáles son las reglas del contrato a término fijo?"
    }
    
    Response:
    {
        "answer": "La respuesta generada...",
        "citations": [...],
        "trace": {...},
        "workflow_trace": {...}
    }
    """
```

#### **rag/agents.py** - Orquestación RAG
- Implementa cadena de RAG
- Gestiona interacción con LLM
- Construye contexto desde documentos recuperados
- Genera respuesta con citas

```python
async def process_query(query: str) -> RAGResponse:
    1. Embeddings de pregunta
    2. Búsqueda en ChromaDB
    3. Selección de fragmentos relevantes
    4. Construcción de contexto legal
    5. Generación con OpenAI
    6. Extracción de citas utilizadas
    7. Cálculo de métricas
```

#### **rag/retriever.py** - Búsqueda Vectorial
- Interfaz con ChromaDB
- Búsqueda de fragmentos similares
- Extracción de metadata
- Scoring de relevancia

#### **rag/llm.py** - Gestión de LLM
- Inicialización de modelos (GPT-4, GPT-3.5)
- Generación de embeddings
- Llamadas a OpenAI API
- Manejo de tokens y límites

#### **db/chroma.py** - Capa de Vectores
- Inicialización de ChromaDB
- Operaciones CRUD
- Indexación de documentos
- Búsqueda por similitud

#### **rag/tools.py** - Herramientas Ejecutables
Implementa 5 tools principales para el RAG:

1. **document_retriever_tool**
   - Busca fragmentos relevantes en la base de conocimiento
   - Utilidad: Recupera contexto legal actual basado en similitud semántica

2. **source_validator_tool**
   - Valida que las citas vengan de fuentes oficiales
   - Utilidad: Previene alucinaciones asegurando citas reales

3. **legal_concept_extractor_tool**
   - Extrae conceptos legales clave de la pregunta
   - Utilidad: Mejora precisión de búsquedas posteriores

4. **context_builder_tool**
   - Ensambla contexto legal coherente de múltiples fragmentos
   - Utilidad: Crea base sólida para generación de respuestas

5. **response_validator_tool**
   - Valida que la respuesta sea consistente con fuentes
   - Utilidad: Asegura que no hay contradicciones con legislación

---

## 6. TIPOS Y ESTRUCTURAS DE DATOS

### 6.1 Types (app/types.ts)

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
    message: str
    conversation_id: Optional[str] = None

class Citation(BaseModel):
    source: str
    page: Optional[int]
    snippet: str
    url: Optional[str]

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    trace: Dict
    workflow_trace: Dict
```

---

## 7. HERRAMIENTAS IMPLEMENTADAS (Tools)

### 7.1 Document Retriever Tool ✓

**¿Por qué es útil?**
- Accede a la base de conocimiento legal sin exponer la API de búsqueda
- Encapsula la lógica de búsqueda vectorial
- Permite que el LLM "invoque" búsquedas cuando necesita contexto
- Mejora la relevancia de respuestas mediante búsqueda semántica

**Implementación**:
```python
def document_retriever_tool(query: str, top_k: int = 3) -> List[Dict]:
    """
    Busca en ChromaDB fragmentos legales relevantes
    
    Input: "contrato a término fijo"
    Output: [
        {
            "source": "DECRETO 1072 DE 2015",
            "page": 200,
            "snippet": "El contrato a término fijo...",
            "relevance_score": 0.87
        },
        ...
    ]
    """
```

### 7.2 Source Validator Tool ✓

**¿Por qué es útil?**
- Previene que el modelo genere citas falsas
- Valida que cada cita provenga de documentos oficiales
- Aumenta confiabilidad del asistente legal
- Detecta alucinaciones antes de retornarlas al usuario

**Implementación**:
```python
def source_validator_tool(citation: Dict) -> ValidationResult:
    """
    Verifica que la cita exista realmente en la base de datos
    
    - Chequea que source + page + snippet coincidan
    - Retorna: { is_valid: bool, confidence: float }
    """
```

### 7.3 Legal Concept Extractor Tool ✓

**¿Por qué es útil?**
- Descomposición de preguntas complejas en conceptos legales
- Mejora búsquedas posteriores con términos específicos
- Identifica los "tópicos legales" principales
- Prepara el contexto para búsquedas más precisas

**Implementación**:
```python
def legal_concept_extractor_tool(question: str) -> List[str]:
    """
    Extrae conceptos legales clave
    
    Input: "¿Cuáles son las reglas básicas del contrato a término fijo?"
    Output: ["contrato a término fijo", "duración", "terminación", "derechos"]
    """
```

### 7.4 Context Builder Tool ✓

**¿Por qué es útil?**
- Ensambla contexto coherente de múltiples fragmentos
- Evita contextos fragmentados o contradictorios
- Organiza información por temas relacionados
- Prepara información optimizada para LLM

**Implementación**:
```python
def context_builder_tool(fragments: List[Dict]) -> str:
    """
    Construye contexto legal coherente
    
    Input: Lista de fragmentos de múltiples decretos
    Output: Contexto organizado por temas con transiciones
    """
```

### 7.5 Response Validator Tool ✓

**¿Por qué es útil?**
- Valida consistencia entre respuesta y fuentes
- Detecta respuestas contradictorias
- Calcula score de confianza
- Añade advertencias si hay dudas

**Implementación**:
```python
def response_validator_tool(response: str, sources: List[Dict]) -> ValidationMetrics:
    """
    Valida que respuesta sea consistente con fuentes
    
    Output: {
        "consistency_score": 0.92,
        "confidence_level": "high",
        "has_contradictions": False,
        "warnings": []
    }
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
│   │   │       │   ├── workflow-trace-panel.tsx  # Panel de trazabilidad
│   │   │       │   └── [otros componentes UI]
│   │   │       └── figma/
│   │   │           └── ImageWithFallback.tsx
│   │   ├── services/
│   │   │   └── chatService.ts       # Cliente HTTP para backend
│   │   ├── mocks/
│   │   │   └── mockService.ts       # Datos mock para desarrollo
│   │   └── styles/
│   │       ├── colors.ts            # Paleta de colores
│   │       ├── traceability.css     # Estilos de paneles
│   │       ├── theme.css
│   │       └── [...otros]
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── rag/                              # Backend Python/FastAPI
│   ├── app/
│   │   ├── main.py                  # Aplicación FastAPI
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── routes.py            # Endpoints: /api/chat, /api/health
│   │   │   └── schemas.py           # Pydantic schemas
│   │   ├── core/
│   │   │   └── config.py            # Configuración (API keys, modelos)
│   │   ├── db/
│   │   │   └── chroma.py            # Interfaz ChromaDB
│   │   ├── rag/
│   │   │   ├── agents.py            # Orquestación RAG
│   │   │   ├── retriever.py         # Búsqueda vectorial
│   │   │   ├── llm.py               # Gestión de modelos
│   │   │   ├── prompts.py           # Templates de prompts
│   │   │   ├── tools.py             # 5 Tools principales
│   │   │   └── pipelines/
│   │   │       └── run_ingestion.py # Ingesta de PDFs
│   │   └── data/
│   │       └── [Documentos legales]
│   │
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_rag.py
│   │   └── __init__.py
│   │
│   ├── db_chroma/                    # Base de datos vectorial
│   │   ├── chroma.sqlite3
│   │   └── [colecciones]
│   │
│   ├── storage/                      # Almacenamiento de documentos
│   │
│   ├── pyproject.toml               # Dependencias Python
│   ├── Makefile                     # Comandos de desarrollo
│   ├── requirements.txt
│   └── README.md
│
├── examples/                         # Ejemplos de uso
├── README.md                         # Documentación principal
├── CONTRIBUTING.md                  # Guía de contribuciones
├── CONSIDERATIONS.md                # Consideraciones de diseño
---

## 8. CONCLUSIÓN

El **SPE AI Labor Law Assistant** es una solución completa que demuestra cómo combinar:
- **IA Generativa** (OpenAI GPT-4)
- **Búsqueda Vectorial** (ChromaDB)
- **Frontend Moderno** (React + TypeScript)
- **Backend Robusto** (FastAPI)

Para crear un **asistente legal especializado** que proporciona respuestas verificables basadas en legislación real.

La arquitectura es modular, testeable y escalable, permitiendo agregar nuevas fuentes legales, mejorar prompts y ajustar las herramientas sin cambios mayores.
