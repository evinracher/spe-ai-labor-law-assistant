# Informe Técnico — Sistema RAG: Asistente de Derecho Laboral Colombiano

> **Fecha:** 25 de febrero de 2026  
> **Estado del sistema:** Milestone actual — Clasificación de intención + Q&A general funcional. Pipeline RAG con recuperación real pendiente de implementación.

---

## Tabla de contenido

1. [Descripción general del sistema](#1-descripción-general-del-sistema)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Diseño del grafo de agentes (LangGraph)](#3-diseño-del-grafo-de-agentes-langgraph)
4. [Descripción de nodos y agentes](#4-descripción-de-nodos-y-agentes)
5. [Selección de modelos LLM: Groq y Gemini](#5-selección-de-modelos-llm-groq-y-gemini)
6. [Corpus legal y base de datos vectorial](#6-corpus-legal-y-base-de-datos-vectorial)
7. [API REST](#7-api-rest)
8. [Configuración del sistema](#8-configuración-del-sistema)
9. [Casos de uso documentados](#9-casos-de-uso-documentados)
10. [Registros de ejecución](#10-registros-de-ejecución)
11. [Estado actual e implementaciones pendientes](#11-estado-actual-e-implementaciones-pendientes)

---

## 1. Descripción general del sistema

El sistema es un chatbot de **Recuperación Aumentada por Generación (RAG)** especializado en derecho laboral colombiano. Permite a los usuarios realizar consultas en lenguaje natural sobre legislación laboral colombiana y recibir respuestas fundamentadas en un corpus documental legal.

El sistema clasifica automáticamente la intención del usuario y enruta la consulta al pipeline apropiado: búsqueda en el corpus legal (RAG) para preguntas del dominio, o respuesta general directa por LLM para preguntas fuera del dominio.

### Stack tecnológico

| Componente | Tecnología | Versión / Modelo |
|---|---|---|
| Framework API | FastAPI + Uvicorn | 0.x |
| Motor de workflows | LangGraph (StateGraph) | — |
| LLM principal | Groq — `llama-3.1-8b-instant` | Meta Llama 3.1 8B |
| LLM alternativo | Google Gemini — `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite |
| Base de datos vectorial | ChromaDB (persistente) | — |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Local |
| Configuración | Pydantic Settings v2 + `.env` | — |
| Frontend | React + Vite + TailwindCSS | — |

---

## 2. Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│                  (chat-ui / POST /chat)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP JSON
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI Backend                          │
│  GET /health   POST /chat   GET /docs (dev)                 │
│                                                              │
│   app/api/routes.py   →   app/api/schemas.py (Pydantic v2) │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               LangGraph StateGraph (agents.py)               │
│                                                              │
│  classifier_node → [domain/summarize/compare/general] →     │
│  rag_node → validate_node → integrate_node                  │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
┌────────────▼────────┐         ┌──────────▼──────────────┐
│   Groq / Gemini LLM │         │  ChromaDB (vectorial)    │
│   (llm.py)          │         │  ⚠ PENDIENTE recuperación│
└─────────────────────┘         │  real de documentos      │
                                └─────────────────────────┘
```

### Flujo de una solicitud

1. El frontend envía `POST /chat` con la pregunta del usuario.
2. `routes.py` decide si usar el mock (desarrollo) o el grafo real (`ask_chat`).
3. El grafo LangGraph clasifica la intención y la enruta.
4. El nodo correspondiente construye el prompt o responde directamente.
5. El `rag_node` invoca al LLM y genera citas (actualmente mock).
6. El `validate_node` verifica la calidad de la respuesta.
7. El `integrate_node` ensambla el `ChatResponse` final.
8. La API retorna JSON con `answer`, `citations` y `trace`.

---

## 3. Diseño del grafo de agentes (LangGraph)

El sistema implementa un `StateGraph` en `app/rag/agents.py`. El grafo compila el flujo de agentes con checkpointing en memoria (`InMemorySaver`) para mantener historial de conversación por `conversation_id`.

### Diagrama del grafo

```
START
  │
  ▼
classifier_node ──────────────────────────────────────────────┐
  │                                                            │
  ├─ intent=domainSearch  ──► domain_search_node              │
  ├─ intent=summarize     ──► summarize_node                  │
  ├─ intent=compare       ──► compare_node                    │
  └─ intent=generalSearch ──► general_search_node             │
           │                          │                        │
           └──────────────────────────┘                        │
                          │                                    │
                          ▼                                    │
                       rag_node          general_search_node ──┘
                          │                       │
                          └───────────┬───────────┘
                                      ▼
                               validate_node
                                      │
                          ┌───────────┴────────────┐
                          │ is_valid=False          │ is_valid=True
                          ▼                         ▼
                       rag_node              integrate_node
                                                    │
                                                   END
```

### Estado compartido del grafo (`GraphState`)

```python
class GraphState(TypedDict):
    messages:  Sequence[BaseMessage]   # historial acumulado de mensajes
    question:  str                     # pregunta clasificada
    intent:    Literal["domainSearch", "summarize", "compare", "generalSearch"]
    rag_prompt: str                    # prompt construido por el nodo de intención
    citations:  list[Citation]         # citas recuperadas del corpus
    is_valid:   bool                   # resultado de la validación de la respuesta
```

---

## 4. Descripción de nodos y agentes

### 4.1 `classifier_node`

**Propósito:** Clasificar la intención del usuario en una de cuatro categorías y extraer la pregunta normalizada.

**LLM usado:** Groq `llama-3.1-8b-instant` con salida estructurada (`with_structured_output(ClassifierOutput)`).

**Modelo de salida:**
```python
class ClassifierOutput(BaseModel):
    question: str   # pregunta original del usuario
    intent: Literal["domainSearch", "summarize", "compare", "generalSearch"]
```

**Prompt del sistema (`CLASSIFIER_PROMPT`):**
```
You are a classifier. Your task is to classify the user intention:
- 'domainSearch':   pregunta sobre derecho laboral colombiano
- 'summarize':      solicitud de resumen de un artículo o ley del dominio
- 'compare':        comparación de dos o más conceptos del dominio legal
- 'generalSearch':  pregunta general fuera del dominio laboral
Answer only with the JSON scheme asked.
```

---

### 4.2 `domain_search_node`

**Propósito:** Construir el prompt RAG para búsquedas de conceptos o preguntas sobre derecho laboral colombiano.

**LLM usado:** Ninguno (nodo de construcción de prompt).

**Prompt generado:**
```
Perform a similarity search in the legal document corpus for the following concept
or question: '{question}'. Using the retrieved fragments, answer precisely as an
expert in Colombian labor law.
```

---

### 4.3 `summarize_node`

**Propósito:** Construir el prompt RAG orientado a resumir artículos o leyes del corpus.

**LLM usado:** Ninguno (nodo de construcción de prompt).

**Prompt generado:**
```
Perform a similarity search in the legal document corpus related to: '{question}'.
Using the retrieved fragments, generate a clear and structured summary of the
legal content found.
```

---

### 4.4 `compare_node`

**Propósito:** Construir el prompt RAG para comparar conceptos jurídicos, estructurando la respuesta en: Definición, Diferencias clave e Implicaciones legales.

**LLM usado:** Ninguno (nodo de construcción de prompt).

**Prompt generado:**
```
Perform a similarity search in the legal document corpus to retrieve information
about the legal concepts present in: '{question}'. Using the retrieved fragments,
compare those concepts in a structured way, organizing the response into:
Definition, Key differences, and Legal implications.
```

---

### 4.5 `general_search_node`

**Propósito:** Responder preguntas fuera del dominio del derecho laboral colombiano directamente mediante el LLM, añadiendo una nota de advertencia.

**LLM usado:** Groq `llama-3.1-8b-instant`.

**Prompt del sistema (`GENERAL_SYSTEM_PROMPT`):**
```
Answer the user question in Spanish. At the end of the answer, only if user asked
a question, add a note that says:

**Nota:** Soy un asistente especializado en **derecho laboral colombiano**.
Esta respuesta se proporciona a nivel general y puede no reflejar información
actualizada o especializada sobre este tema. Se recomienda consultar una fuente
experta o profesional en el área correspondiente.
```

---

### 4.6 `rag_node`

**Propósito:** Ejecutar el LLM con el prompt RAG construido por el nodo de intención y generar las citas del corpus.

**LLM usado:** Groq `llama-3.1-8b-instant`.

**⚠ Implementación actual (mock):** Las citas se generan mediante la herramienta `generate_mock_citations` (selección determinista por hash MD5 de la pregunta). La recuperación real desde ChromaDB está pendiente.

**Comportamiento:**
- Si existe `rag_prompt` en el estado → invoca el LLM con el prompt + instrucción de responder en español.
- Si no hay `rag_prompt` (reintento por validación fallida) → invoca el LLM con el historial de mensajes directamente.
- Genera hasta `MAX_CITATIONS = 5` citas del pool mock.

---

### 4.7 `validate_node`

**Propósito:** Verificar que la respuesta generada sea válida antes de entregarla al usuario.

**LLM usado:** Ninguno.

**⚠ Implementación actual (simplificada):** Verifica únicamente que la respuesta no contenga la cadena `"No sé"`. Si la contiene, `is_valid = False` y el grafo reintenta con `rag_node`.

**⚠ Pendiente:** Implementar validación real (verificación de alucinaciones, coherencia con las citas recuperadas, detección de respuestas vacías).

---

### 4.8 `integrate_node`

**Propósito:** Ensamblar la respuesta final extrayendo los campos relevantes del estado del grafo y retornarlos al caller `ask_chat`.

**LLM usado:** Ninguno.

**Retorna:** `answer`, `question`, `intent`, `citations`.

---

## 5. Selección de modelos LLM: Groq y Gemini

### 5.1 Groq — `llama-3.1-8b-instant`

Groq es el proveedor LLM **activo por defecto** en el sistema. Se instancia directamente en `agents.py` y también está disponible vía `llm.py` cuando `LLM_PROVIDER=groq`.

```python
grop_LLM = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=settings.GROQ_API_KEY,
)
```

**Justificación de la selección:**

| Criterio | Razón |
|---|---|
| **Velocidad de inferencia** | Groq utiliza hardware LPU (*Language Processing Unit*) propio, alcanzando 500–700 tokens/s frente a 50–100 tokens/s de una GPU convencional. Esencial para un chatbot interactivo en tiempo real. |
| **Latencia ultrabaja** | Las respuestas se perciben como instantáneas desde el frontend React, lo que mejora significativamente la experiencia de usuario. |
| **Costo en desarrollo** | La API de Groq ofrece un tier gratuito con límites generosos, ideal para prototipado académico sin incurrir en costos. |
| **Modelo Llama 3.1 8B** | El modelo de Meta es suficientemente capaz para: (a) clasificación de intenciones con output estructurado Pydantic, (b) generación de respuestas legales en español con temperatura baja (0.2) para mayor determinismo y precisión. |
| **Integración LangChain** | `langchain_groq.ChatGroq` implementa `BaseChatModel`, siendo compatible de forma nativa con LangGraph sin adaptadores adicionales. |
| **Soporte de structured output** | `ChatGroq.with_structured_output(ClassifierOutput)` garantiza que el clasificador siempre retorne JSON válido y tipado, eliminando parsing manual. |

**Agentes donde se usa Groq:**
- `classifier_node` — clasificación de intención con output estructurado
- `general_search_node` — respuestas a preguntas generales
- `rag_node` — generación de respuestas sobre derecho laboral

---

### 5.2 Gemini — `gemini-2.5-flash-lite`

Gemini está disponible como proveedor alternativo configurable vía `LLM_PROVIDER=gemini` en el archivo `.env`. Se instancia en `app/rag/llm.py` mediante la función singleton `get_llm()`.

```python
_llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash-lite",
    temperature=0.2,
    google_api_key=settings.GEMINI_API_KEY,
)
```

**Justificación de la selección:**

| Criterio | Razón |
|---|---|
| **Ventana de contexto extendida** | Gemini 2.5 Flash soporta contextos de hasta 1M tokens, lo que permite en futuros milestones ingerir documentos legales completos (CST, Ley 100, Decreto 1072) como contexto directo del prompt. |
| **Capacidad multimodal** | Potencial para procesar PDFs del corpus directamente sin OCR previo, reduciendo complejidad en la pipeline de ingestión. |
| **Variante Flash Lite** | Optimizada para velocidad y costo, manteniendo calidad suficiente para comprensión y generación de texto legal en español. |
| **Redundancia y resiliencia** | Al soportar dos proveedores, el sistema puede cambiar entre Groq y Gemini si alguno alcanza sus límites de rate o presenta interrupciones de servicio. |
| **Integración LangChain** | `langchain_google_genai.ChatGoogleGenerativeAI` implementa la misma interfaz `BaseChatModel`, permitiendo intercambiar proveedores sin modificar la lógica del grafo. |

**Agentes donde se usa Gemini:** Todos los que actualmente usan Groq, cuando `LLM_PROVIDER=gemini` está configurado. El sistema es agnóstico al proveedor gracias al patrón singleton de `get_llm()`.

---

### 5.3 Comparativa de proveedores

| Característica | Groq (llama-3.1-8b-instant) | Gemini (2.5-flash-lite) |
|---|---|---|
| Velocidad | ⚡ Muy alta (LPU) | 🔶 Alta (GPU Google) |
| Ventana de contexto | 128K tokens | 1M tokens |
| Costo en desarrollo | Gratuito (tier free) | Gratuito con límites |
| Soporte structured output | ✅ Nativo | ✅ Nativo |
| Multimodal (PDF) | ❌ No | ✅ Sí |
| Uso actual en el sistema | ✅ Por defecto (activo) | 🔄 Alternativo (configurable) |

---

## 6. Corpus legal y base de datos vectorial

### 6.1 Fuentes legales del corpus

El sistema trabaja sobre documentos del marco normativo del trabajo en Colombia. Las fuentes del corpus de referencia incluyen:

| Fuente | Descripción |
|---|---|
| `CST_codigo_sustantivo_trabajo.pdf` | Código Sustantivo del Trabajo — norma fundamental del derecho laboral colombiano |
| `ley_789_2002_reforma_laboral.pdf` | Ley 789 de 2002 — reforma laboral, jornada, auxilio de transporte |
| `ley_1468_2011_licencia_maternidad.html` | Ley 1468 de 2011 — licencia de maternidad (18 semanas) |
| `decreto_1072_2015_reglamento_trabajo.pdf` | Decreto 1072 de 2015 — Decreto Único Reglamentario del Sector Trabajo |
| `ley_100_1993_seguridad_social.pdf` | Ley 100 de 1993 — Sistema de Seguridad Social Integral |
| Constitución Política — Art. 53 | Principios fundamentales del trabajo |

### 6.2 Base de datos vectorial — ChromaDB

- **Motor:** ChromaDB (cliente persistente)
- **Directorio:** `./storage/chroma`
- **Colección:** `labor_law`
- **Inicialización:** En el evento `startup` de FastAPI, se crea o carga la colección `labor_law`.

```python
chroma_client = get_chroma_client()  # chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name="labor_law")
```

### 6.3 Modelo de embeddings

- **Modelo:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Ejecución:** Local (sin API externa)
- **Soporte multilingüe:** Optimizado para español y otros idiomas

**⚠ Estado actual:** La colección `labor_law` se inicializa vacía. La ingestión de documentos y el cálculo de embeddings están **pendientes de implementación**.

### 6.4 Pool de citas mock (estado actual)

Mientras la recuperación real no esté implementada, el `rag_node` genera citas usando la herramienta `generate_mock_citations` con un pool de 7 fragmentos reales de la legislación:

| Fuente | Fragmento |
|---|---|
| CST, Art. 57 | Obligación del empleador de suministrar útiles y materiales al trabajador |
| Ley 50/1990, Art. 22 | 15 días hábiles consecutivos de vacaciones remuneradas por año |
| Decreto 1072/2015, Art. 2.2.1 | Respeto a la dignidad, igualdad y no discriminación |
| Ley 100/1993, Art. 15 | Afiliación obligatoria al Sistema General de Pensiones |
| CST, Art. 140 | Descanso remunerado en días de fiesta |
| Ley 789/2002, Art. 5 | Auxilio de transporte para salarios ≤ 2 SMMLV |
| Constitución Política, Art. 53 | Estatuto del trabajo e igualdad de oportunidades |

La selección de citas es **determinista**: se usa `hashlib.md5(question)` como semilla del shuffle, garantizando que la misma pregunta siempre retorne las mismas citas (útil para pruebas).

---

## 7. API REST

### 7.1 Endpoints disponibles

| Método | Ruta | Descripción | Estado |
|---|---|---|---|
| `GET` | `/health` | Liveness probe | ✅ Implementado |
| `POST` | `/chat` | Chatbot RAG de derecho laboral | ✅ Implementado (mock/LLM) |
| `GET` | `/docs` | Swagger UI (solo `ENV=dev`) | ✅ Disponible en dev |
| `POST` | `/ingest` | Ingestión del corpus | ⚠ **Pendiente** |
| `GET` | `/chat/{id}/history` | Historial de conversación | ⚠ **Pendiente** |
| `DELETE` | `/chat/{id}` | Limpiar conversación | ⚠ **Pendiente** |

### 7.2 Esquemas Pydantic v2

#### Request — `ChatRequest`

```python
class ChatRequest(BaseModel):
    question:        str       # max 2000 chars, no puede estar en blanco
    conversation_id: str|None  # agrupa turnos en una conversación
    max_citations:   int|None  # 1-20, default al setting del servidor
```

#### Response — `ChatResponse`

```python
class ChatResponse(BaseModel):
    ok:          bool          # True si la solicitud fue procesada
    request_id:  str           # UUID único por solicitud
    answer:      str           # respuesta en español
    citations:   list[Citation]
    trace:       Trace

class Citation(BaseModel):
    source:    str             # nombre del documento fuente
    page:      int|None        # número de página
    chunk_id:  str|None        # identificador interno del chunk
    snippet:   str             # fragmento textual verbatim

class Trace(BaseModel):
    intent:    str|None        # intención clasificada
    top_k:     int|None        # número de chunks recuperados
    vector_db: str             # backend vectorial usado
```

### 7.3 Enrutamiento en `routes.py`

```python
if settings.LLM_PROVIDER == "mock":
    return mock_rag_answer(question=body.question, settings=settings)
# LLM_PROVIDER = "groq" | "gemini" | "local"
return ask_chat(question=body.question, settings=settings, conversation_id=body.conversation_id)
```

---

## 8. Configuración del sistema

El sistema se configura mediante variables de entorno o archivo `.env` (Pydantic Settings v2):

| Variable | Default | Descripción |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `groq` / `gemini` / `local` / `mock` |
| `GROQ_API_KEY` | `None` | Requerido si `LLM_PROVIDER=groq` |
| `GEMINI_API_KEY` | `None` | Requerido si `LLM_PROVIDER=gemini` |
| `VECTOR_DB` | `chroma` | Backend de base de datos vectorial |
| `CHROMA_DIR` | `./storage/chroma` | Directorio persistente de ChromaDB |
| `DATA_DIR` | `./data` | Directorio con archivos del corpus (PDF/HTML/TXT) |
| `EMBEDDINGS_PROVIDER` | `local` | Backend de embeddings |
| `EMBEDDINGS_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo local multilingüe |
| `HOST` | `0.0.0.0` | Host de bind del servidor |
| `PORT` | `8000` | Puerto de bind del servidor |
| `ENV` | `dev` | `dev` o `prod` (activa/desactiva Swagger UI) |

---

## 9. Casos de uso documentados

### Caso de uso 1 — Consulta sobre vacaciones laborales

**Pregunta:** `¿Cuántos días de vacaciones tiene derecho un trabajador en Colombia?`

**Intención clasificada:** `domainSearch`

**Flujo:**
```
classifier_node → domain_search_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada (mock):**
> Según el Código Sustantivo del Trabajo colombiano, todo trabajador que haya prestado sus servicios durante un año continuo tiene derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas (artículo 186 CST). Durante el período vacacional, el empleador debe pagar el salario ordinario que el trabajador esté devengando al momento en que comience a disfrutar de sus vacaciones (artículo 189 CST)...

**Citas retornadas (mock):** Ley 50/1990 Art. 22, CST Art. 57.

**`trace.intent`:** `domainSearch`

---

### Caso de uso 2 — Consulta sobre obligaciones del empleador

**Pregunta:** `¿Cuáles son las obligaciones del empleador según el Código Sustantivo del Trabajo?`

**Intención clasificada:** `domainSearch`

**Flujo:**
```
classifier_node → domain_search_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada:** Descripción de obligaciones del empleador según el CST Art. 57, incluyendo suministro de materiales, respeto a la dignidad del trabajador, pago oportuno de salarios.

**Citas retornadas (mock):** CST Art. 57, Decreto 1072/2015.

---

### Caso de uso 3 — Consulta sobre auxilio de transporte

**Pregunta:** `¿A quiénes aplica el auxilio de transporte en Colombia?`

**Intención clasificada:** `domainSearch`

**Flujo:**
```
classifier_node → domain_search_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada:** El auxilio de transporte aplica a trabajadores cuya remuneración mensual no exceda dos salarios mínimos legales vigentes, según Ley 789 de 2002 Art. 5.

**Citas retornadas (mock):** Ley 789/2002 Art. 5.

---

### Caso de uso 4 — Resumen de artículo de ley

**Pregunta:** `Resume el artículo 53 de la Constitución Política de Colombia`

**Intención clasificada:** `summarize`

**Flujo:**
```
classifier_node → summarize_node → rag_node → validate_node → integrate_node
```

**Prompt RAG generado por `summarize_node`:**
```
Perform a similarity search in the legal document corpus related to:
'Resume el artículo 53 de la Constitución Política de Colombia'.
Using the retrieved fragments, generate a clear and structured summary
of the legal content found.
```

**Respuesta esperada:** Resumen estructurado del Art. 53, incluyendo los principios mínimos del trabajo: igualdad de oportunidades, remuneración mínima, estabilidad en el empleo, irrenunciabilidad de beneficios, etc.

**Citas retornadas (mock):** Constitución Política Art. 53.

---

### Caso de uso 5 — Resumen de ley completa

**Pregunta:** `¿De qué trata la Ley 100 de 1993?`

**Intención clasificada:** `summarize`

**Flujo:**
```
classifier_node → summarize_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada:** Resumen del Sistema de Seguridad Social Integral: sistema de pensiones, afiliación obligatoria para trabajadores vinculados por contrato de trabajo, cobertura de vejez, invalidez y muerte.

**Citas retornadas (mock):** Ley 100/1993 Art. 15.

---

### Caso de uso 6 — Comparación de conceptos jurídicos

**Pregunta:** `¿Cuál es la diferencia entre contrato a término fijo e indefinido?`

**Intención clasificada:** `compare`

**Flujo:**
```
classifier_node → compare_node → rag_node → validate_node → integrate_node
```

**Prompt RAG generado por `compare_node`:**
```
Perform a similarity search in the legal document corpus to retrieve information
about the legal concepts present in: '¿Cuál es la diferencia entre contrato a
término fijo e indefinido?'. Using the retrieved fragments, compare those concepts
in a structured way, organizing the response into: Definition, Key differences,
and Legal implications.
```

**Respuesta esperada:** Tabla o sección estructurada con: Definición de cada tipo, diferencias en duración, preaviso, causales de terminación, e implicaciones legales para indemnizaciones.

---

### Caso de uso 7 — Comparación entre leyes

**Pregunta:** `Compara la Ley 50 de 1990 con el CST en materia de vacaciones`

**Intención clasificada:** `compare`

**Flujo:**
```
classifier_node → compare_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada:** Comparativa entre la regulación original del CST y las modificaciones introducidas por la Ley 50/1990 respecto a días de vacaciones, acumulación y compensación en dinero.

---

### Caso de uso 8 — Consulta sobre seguridad social

**Pregunta:** `¿Tiene derecho un trabajador informal a seguridad social?`

**Intención clasificada:** `domainSearch`

**Flujo:**
```
classifier_node → domain_search_node → rag_node → validate_node → integrate_node
```

**Respuesta esperada:** Explicación de la obligación de afiliación desde el primer día de vinculación laboral, porcentajes de aportes a EPS, AFP y ARL, con base en Decreto 1072/2015 y Ley 100/1993.

**Citas retornadas (mock):** Ley 100/1993 Art. 15, Decreto 1072/2015.

---

### Caso de uso 9 — Pregunta general fuera del dominio laboral

**Pregunta:** `¿Cuántos planetas tiene el sistema solar?`

**Intención clasificada:** `generalSearch`

**Flujo:**
```
classifier_node → general_search_node → validate_node → integrate_node
```

**Respuesta esperada:** Respuesta general correcta en español (8 planetas), seguida de la nota de advertencia:
> **Nota:** Soy un asistente especializado en **derecho laboral colombiano**. Esta respuesta se proporciona a nivel general y puede no reflejar información actualizada o especializada sobre este tema. Se recomienda consultar una fuente experta o profesional en el área correspondiente.

**Citas retornadas:** Lista vacía `[]`.

---

### Caso de uso 10 — Pregunta de cocina (fuera del dominio)

**Pregunta:** `¿Cómo se hace una receta de arepas?`

**Intención clasificada:** `generalSearch`

**Flujo:**
```
classifier_node → general_search_node → validate_node → integrate_node
```

> **Nota (mock):** En modo `LLM_PROVIDER=mock`, el sistema detecta la palabra `"receta"` como keyword fuera de contexto y retorna directamente: `"No aparece en el contexto."` con `citations: []`. En modo LLM real (`groq`/`gemini`), el clasificador asigna `generalSearch` y responde con el LLM + nota de advertencia.

---

### Caso de uso 11 — Reintento automático por respuesta inválida

**Escenario:** El `rag_node` genera una respuesta que contiene la cadena `"No sé"`.

**Flujo:**
```
rag_node → validate_node (is_valid=False) → rag_node (reintento) → validate_node (is_valid=True) → integrate_node
```

**Comportamiento:** El grafo reintenta automáticamente la generación de respuesta sin intervención del usuario. El loop máximo depende de la lógica del grafo (actualmente sin límite explícito de reintentos).

**⚠ Pendiente:** Implementar un contador de reintentos máximo para evitar loops infinitos.

---

### Caso de uso 12 — Conversación con memoria múltiple turno

**Escenario:** El usuario envía varias preguntas usando el mismo `conversation_id`.

**Request turno 1:**
```json
{ "question": "¿Cuántos días de vacaciones tiene un trabajador?", "conversation_id": "conv-abc-123" }
```
**Request turno 2:**
```json
{ "question": "¿Y si lleva solo 6 meses trabajando?", "conversation_id": "conv-abc-123" }
```

**Comportamiento:** El `InMemorySaver` almacena el historial de mensajes por `thread_id = conversation_id`. El segundo turno tiene acceso al contexto del primero, permitiendo preguntas de seguimiento contextuales.

**⚠ Limitación actual:** La memoria es **en RAM**, no persistente. Se pierde al reiniciar el servidor.

---

## 10. Registros de ejecución

### 10.1 Logs de inicio del servidor

Al ejecutar `LLM_PROVIDER=groq uvicorn app.main:app --reload`:

```
✅ grop_LLM ready: llama-3.1-8b-instant
2026-02-25T10:00:01 | INFO     | app.main | Starting Colombian Labor Law RAG backend | env=dev | provider=groq | vector_db=chroma
2026-02-25T10:00:01 | INFO     | app.main | CHROMA_DIR=./storage/chroma | DATA_DIR=./data
2026-02-25T10:00:01 | INFO     | app.main | ChromaDB ready | collection=labor_law | docs=0
```

### 10.2 Trazas de una solicitud `domainSearch`

```
🚨 PROVIDER ACTUAL: groq
🔥 ENTRANDO A ask_chat
[DEBUG]: domain_search_node
[DEBUG]: rag_node — intent=domainSearch
[DEBUG]: rag_node using rag_prompt: Perform a similarity search...
[DEBUG]: rag_node — generated 5 citations
[DEBUG]: validate_node — answer is valid
[DEBUG]: integrate_node
```

### 10.3 Trazas de reintento por respuesta inválida

```
[DEBUG]: rag_node — intent=domainSearch
[DEBUG]: rag_node — generated 5 citations
[DEBUG]: validate_node — answer is NOT valid, will retry with RAG node
[DEBUG]: rag_node — intent=domainSearch
[DEBUG]: rag_node — generated 5 citations
[DEBUG]: validate_node — answer is valid
[DEBUG]: integrate_node
```

### 10.4 Ejemplo de respuesta JSON completa

```json
{
  "ok": true,
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "answer": "Según el Código Sustantivo del Trabajo colombiano, todo trabajador que haya prestado sus servicios durante un año continuo tiene derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas (artículo 186 CST)...",
  "citations": [
    {
      "source": "Ley 50 de 1990",
      "page": 12,
      "chunk_id": "ley50-art-22",
      "snippet": "El trabajador tiene derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas por cada año de servicios."
    },
    {
      "source": "Código Sustantivo del Trabajo (CST)",
      "page": 57,
      "chunk_id": "cst-art-57",
      "snippet": "El empleador está obligado a suministrar al trabajador los útiles, materiales e instrumentos necesarios para la realización de las labores."
    }
  ],
  "trace": {
    "intent": "domainSearch",
    "top_k": 2,
    "vector_db": "chroma"
  }
}
```

---

## 11. Estado actual e implementaciones pendientes

### ✅ Implementado y funcional

- Servidor FastAPI con CORS, Swagger UI en modo dev y eventos de startup/shutdown.
- Grafo LangGraph con 8 nodos, enrutamiento condicional y memoria en RAM por `conversation_id`.
- Clasificador de intenciones con output estructurado Pydantic (Groq).
- Nodos de construcción de prompts para `domainSearch`, `summarize` y `compare`.
- Respuestas generales fuera del dominio con nota de advertencia (Groq).
- Generación de respuestas RAG con LLM (Groq), forzando idioma español.
- Validación básica de respuestas con reintento automático.
- Soporte de dos proveedores LLM intercambiables (Groq / Gemini) vía variable de entorno.
- ChromaDB inicializado en startup (colección `labor_law` creada, vacía).
- Pool de citas mock deterministas para pruebas frontend.
- Responder mock determinista para `LLM_PROVIDER=mock` (desarrollo sin API keys).

---

### ⚠ Pendiente de implementación

| # | Funcionalidad | Módulo | Prioridad |
|---|---|---|---|
| 1 | **Pipeline de ingestión del corpus** — cargar PDF/HTML/TXT desde `DATA_DIR`, limpiar texto, dividir en chunks (512 tokens, 64 overlap), calcular embeddings locales, persistir en ChromaDB. | `app/rag/ingest.py` (nuevo) | Alta |
| 2 | **Recuperación real desde ChromaDB** — en `rag_node`, reemplazar `generate_mock_citations` por búsqueda de similitud vectorial real contra la colección `labor_law`. Retornar `Citation` con fragmentos reales. | `agents.py` — `rag_node` | Alta |
| 3 | **Prompt estricto anti-alucinación** — fortalecer el system prompt del `rag_node` para que el LLM responda *exclusivamente* con base en los fragmentos recuperados; si la información no está en el corpus, retornar exactamente: `"No aparece en el contexto."` | `prompts.py` | Alta |
| 4 | **Validación real en `validate_node`** — verificar que la respuesta esté fundamentada en las citas recuperadas, detectar alucinaciones, verificar coherencia. Actualmente solo verifica ausencia de `"No sé"`. | `agents.py` — `validate_node` | Media |
| 5 | **Límite de reintentos en el loop de validación** — agregar contador para evitar loops infinitos cuando `validate_node` rechaza repetidamente. | `agents.py` — `validate_route` | Media |
| 6 | **Endpoint `POST /ingest`** — disparar la ingestión del corpus bajo demanda, o script CLI `python -m app.ingest`. | `app/api/ingest_routes.py` (nuevo) | Media |
| 7 | **Warm-up del modelo de embeddings en startup** — cargar `sentence-transformers` al iniciar la aplicación para evitar latencia en la primera solicitud. | `app/main.py` — `on_startup` | Media |
| 8 | **Persistencia de historial de conversación** — actualmente `InMemorySaver` se pierde al reiniciar. Implementar persistencia con base de datos (SQLite / Redis). | `agents.py` | Baja |
| 9 | **Endpoint `GET /chat/{id}/history`** — retornar el historial de turnos de una conversación. | `app/api/routes.py` | Baja |
| 10 | **Soporte LLM local (Ollama)** — implementar `LLM_PROVIDER=local` para ejecución offline con modelos locales. | `app/rag/llm.py` | Baja |
| 11 | **Tightening CORS en producción** — actualmente `allow_origins=["*"]` en dev. Restringir a orígenes permitidos para despliegue en red. | `app/main.py` | Alta (producción) |
| 12 | **Pruebas de integración del pipeline RAG real** — test que un corpus real retorne citas reales, test de `"No aparece en el contexto."` para preguntas fuera del corpus. | `tests/test_pipeline.py` (nuevo) | Media |

---

*Informe generado con base en el análisis del código fuente del repositorio `spe-ai-labor-law-assistant` — rama principal, estado al 25 de febrero de 2026.*
