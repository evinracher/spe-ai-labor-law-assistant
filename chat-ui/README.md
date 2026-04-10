
  # Labor Law Assistant - Chat UI

A modern React-based chat interface for the AI Labor Law Assistant. This application provides an intuitive user experience for interacting with the Colombian labor law chatbot, supporting both specialized labor law queries and general questions.

## 🎨 Features

- 💬 Real-time chat interface with message bubbles and inline **bold** markdown rendering
- 🎯 Seamless integration with the RAG backend API
- 💾 Persistent conversation history using localStorage
- 🎨 Modern UI with Radix UI and Material-UI components
- 📱 Responsive design for desktop and mobile
- 📚 Collapsible citations panel with links to legal source documents
- ⚙️ Collapsible workflow trace panel showing backend execution steps, tool calls, and validation results
- ⚡ Fast development with Vite and Hot Module Replacement (HMR)

## 🛠️ Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **UI Components**: 
  - Radix UI (accessible component primitives)
  - Material-UI (MUI) for icons and additional components
- **Styling**: 
  - Tailwind CSS
  - Emotion (CSS-in-JS)
- **Additional Libraries**:
  - lucide-react (icons)
  - date-fns (date utilities)
  - motion (animations)
  - cmdk (command palette)

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

Create a `.env.local` file in the `chat-ui/` directory:

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
│   │   ├── App.tsx              # Main application component
│   │   ├── types.ts             # TypeScript type definitions (Message, Citation, WorkflowTrace…)
│   │   ├── utils/
│   │   │   └── sourceLinks.ts   # Citation source → display name / GitHub URL helpers
│   │   └── components/
│   │       ├── figma/           # Figma-imported components
│   │       └── ui/
│   │           ├── header.tsx               # Fixed app bar with logo and clear-chat button
│   │           ├── message-bubble.tsx       # Chat bubble with markdown and CitationsPanel
│   │           ├── citations-panel.tsx      # Collapsible legal sources panel
│   │           ├── workflow-trace-panel.tsx # Collapsible backend execution trace panel
│   │           ├── empty-state.tsx          # Illustration shown before first message
│   │           └── app-snackbar.tsx         # Error/success snackbar
│   ├── services/
│   │   └── chatService.ts       # API client for backend + conversation ID management
│   ├── mocks/
│   │   └── mockService.ts       # Mock responses for development
│   └── styles/
│       ├── index.css            # Global styles
│       ├── fonts.css            # Font imports
│       ├── tailwind.css         # Tailwind imports
│       ├── theme.css            # Theme variables
│       ├── colors.ts            # Shared color tokens (COLORS object)
│       └── muiTheme.ts          # Material-UI theme
├── index.html                    # HTML entry point
├── vite.config.ts               # Vite configuration
└── package.json                 # Dependencies and scripts
```

## 🔌 API Integration

The chat interface communicates with the backend API through the `chatService.ts` module:

- **Endpoint**: `POST /chat`
- **Request**: 
  ```json
  {
    "question": "string",
    "conversation_id": "string (optional)",
    "max_citations": "number (optional)"
  }
  ```
- **Response**: Returns the answer, citations, trace (intent, top_k, vector_db, llm_provider), and optional workflow_trace

Conversation IDs are automatically generated via `crypto.randomUUID()` and stored in localStorage to maintain conversation context across sessions.

## 🎨 Design

This project was designed in Figma. The original design is available at:
https://www.figma.com/design/g0IeqeYWfcyYCMUPH1gbJL/Single-page-React-Chat-UI

## 📝 Usage

1. Type your question in the chat input field at the bottom
2. Press Enter or click the send button
3. The assistant will process your question and respond with:
   - For labor law questions: Detailed answers based on Colombian labor legislation with citations
   - For general questions: Direct answers using the AI model
4. Your conversation history is preserved across browser sessions

## 🧪 Development

The application uses Vite's fast HMR for rapid development. Changes to source files are reflected immediately in the browser.

### Mock Mode

If the backend API is not available, the application automatically falls back to mock responses defined in `src/mocks/mockService.ts`.
  