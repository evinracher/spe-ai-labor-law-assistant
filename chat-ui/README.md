# Labor Law Assistant - Chat UI

A React-based chat interface for the AI Labor Law Assistant. Provides an intuitive experience for interacting with the Colombian labor law chatbot, with full traceability of retrieved legal sources and agent execution steps.

## 🎨 Features

- 💬 Real-time chat interface with user and assistant message bubbles
- ✍️ Markdown-style bold rendering inside assistant messages
- ⏳ Animated typing indicator while waiting for the backend response
- 📜 **Citations panel** — expandable list of legal sources used in each answer (source name, page number, text snippet; links to GitHub source when available)
- ⚙️ **Workflow trace panel** — collapsible breakdown of every tool step executed by the backend agent (tool name, status, duration, validation score)
- 📝 **Technical sheet modal** — in-app project documentation with PDF download and print support (via `html2pdf.js`)
- 💡 **Empty state** with three clickable suggestion chips to start a conversation
- 🖨️ **Toast notifications** via `AppSnackbar` for API errors
- 💾 Persistent conversation ID stored in `localStorage` for multi-turn context
- 🔄 Automatic fallback to mock responses when the backend is unreachable

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | React 18 + TypeScript |
| Build tool | Vite 6 + HMR |
| UI components | Material-UI (MUI) v7 |
| Primitive components | Radix UI |
| Styling | Tailwind CSS + Emotion (CSS-in-JS) |
| Icons | MUI Icons, lucide-react |
| Animations | Framer Motion (`motion`) |
| PDF export | html2pdf.js |
| Date formatting | date-fns |
| Command palette | cmdk |

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see [rag/README.md](../rag/README.md))

### Installation

```bash
# Navigate to the chat-ui directory
cd chat-ui

# Install dependencies
npm install
```

### Configuration

Create a `.env` file in the `chat-ui/` directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

If `VITE_API_URL` is not set, the application will fall back to mock responses for development.

### Running the Development Server

```bash
# Start the development server
npm run dev
```

The application will be available at `http://localhost:5173` (or another port if 5173 is in use).

### Building for Production

```bash
# Build the application
npm run build

# Preview the production build
npm run preview
```

The built files will be in the `dist/` directory.

## 📁 Project Structure

```
chat-ui/
├── src/
│   ├── app/
│   │   ├── App.tsx                        # Root component: state, send/receive logic
│   │   ├── TechnicalSheetPage.tsx         # Standalone technical sheet route
│   │   ├── types.ts                       # Shared TypeScript interfaces
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── message-bubble.tsx         # User / assistant / typing bubbles
│   │   │   │   ├── citations-panel.tsx        # Expandable legal sources panel
│   │   │   │   ├── workflow-trace-panel.tsx   # Collapsible agent execution trace
│   │   │   │   ├── header.tsx                 # App bar with clear-chat + tech sheet
│   │   │   │   ├── empty-state.tsx            # Intro screen with suggestion chips
│   │   │   │   ├── app-snackbar.tsx           # Toast notification wrapper
│   │   │   │   ├── technical-sheet.tsx        # In-modal tech sheet with PDF export
│   │   │   │   └── [Radix UI / shadcn primitives]
│   │   │   └── figma/
│   │   │       └── ImageWithFallback.tsx
│   │   └── utils/
│   │       └── sourceLinks.ts             # Maps source names → display labels & URLs
│   ├── services/
│   │   └── chatService.ts             # HTTP client for POST /chat
│   ├── mocks/
│   │   └── mockService.ts             # Deterministic mock responses
│   └── styles/
│       ├── colors.ts                  # Central colour palette
│       ├── muiTheme.ts                # Material-UI custom theme
│       ├── traceability.css           # Styles for citations & trace panels
│       ├── theme.css                  # CSS custom properties
│       └── index.css                  # Global resets
├── index.html
├── vite.config.ts
└── package.json
```

## 🔌 API Integration

All backend communication goes through `src/services/chatService.ts`.

**Endpoint**: `POST /chat`

**Request**
```json
{
  "question": "string",
  "conversation_id": "string (optional)",
  "max_citations": "number (optional)"
}
```

**Response**
```json
{
  "ok": true,
  "request_id": "uuid",
  "answer": "string",
  "citations": [
    { "source": "DECRETO 1072 DE 2015", "page": 200, "chunk_id": "chunk_42", "snippet": "..." }
  ],
  "trace": { "intent": "domainSearch", "top_k": 4, "vector_db": "chroma", "llm_provider": "groq" },
  "workflow_trace": {
    "conversation_id": "uuid",
    "total_steps": 5,
    "tools_used": ["classify_intent", "semantic_search", "generate_grounded_answer", "validate_answer"],
    "tool_traces": [ { "tool_name": "...", "status": "success", "duration_ms": 120 } ],
    "validation_passed": true,
    "validation_details": { "coherence_score": 0.91, "grounding_score": 0.87, "hallucination_detected": false }
  }
}
```

A `conversation_id` is auto-generated on first load and persisted in `localStorage`. It is sent on every request to maintain multi-turn context on the backend.

## 🧙 Key Components

### `MessageBubble`
Renders a single chat turn. Handles four roles: `user`, `assistant`, `typing`, and `error`. Assistant bubbles support inline `**bold**` markdown and embed `CitationsPanel` and `WorkflowTracePanel` when the response includes the corresponding data.

### `CitationsPanel`
Expandable panel attached to assistant messages that contain legal citations. Groups results under a "Fuentes Legales" header with a count badge. Each citation shows the document name (with a GitHub link when available via `sourceLinks.ts`), page number, and the exact text snippet retrieved from ChromaDB.

### `WorkflowTracePanel`
Collapsible panel (collapsed by default) that exposes the backend agent execution trace. Shows each tool step with its name, success/failure status icon, and execution duration. Displays overall validation pass/fail and coherence/grounding scores from the `validate_answer` tool.

### `Header`
Fixed app bar with the application title and two action buttons: clear conversation (with confirmation) and open the in-app Technical Sheet modal.

### `EmptyState`
Shown when there are no messages. Displays three pre-built suggestion chips (`Contrato a término fijo`, `Despido con justa causa`, `Liquidación de prestaciones`) that prefill the input on click.

### `TechnicalSheet`
Full project technical documentation rendered inside a `Dialog`. Includes a **Download PDF** button (powered by `html2pdf.js`) and a **Print** button.

## 🎨 Design

Original design created in Figma:
https://www.figma.com/design/g0IeqeYWfcyYCMUPH1gbJL/Single-page-React-Chat-UI

## 📝 Usage

1. Open `http://localhost:5173` in your browser.
2. Type a question or click one of the suggestion chips.
3. The assistant responds with:
   - The generated answer (with inline bold formatting)
   - A **Fuentes Legales** panel listing the legal fragments used
   - A **Detalles del Procesamiento** panel showing which agent tools ran and their duration
4. Conversation history is preserved across browser sessions via `localStorage`.

## 🧪 Development

Vite's HMR reflects source changes immediately in the browser.

### Mock Mode

When `VITE_API_URL` is not set, `chatService.ts` falls back to `src/mocks/mockService.ts`, which returns deterministic mock responses — no backend required for UI development.