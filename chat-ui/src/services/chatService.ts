import { mockResponse } from "../mocks/mockService";
interface Citation {
  source: string;
  page: number | null;
  chunk_id: string | null;
  snippet: string;
}

interface Trace {
  intent: string | null;
  top_k: number | null;
  vector_db: string;
  llm_provider: string;
}

interface ChatResponse {
  ok: boolean;
  request_id: string;
  answer: string;
  citations: Citation[];
  trace: Trace;
}

interface ChatRequest {
  question: string;
  conversation_id?: string;
  max_citations?: number;
}

const API_URL = import.meta.env.VITE_API_URL as string;



export async function sendMessageRequest(
  question: string,
  conversationId?: string,
  maxCitations?: number
): Promise<string> {
  // Ensure we have a conversation id: use provided one or get/create from localStorage
  const convId = conversationId ?? getOrCreateConversationId();

  if (API_URL) {
    const body: ChatRequest = { question };
    if (convId) body.conversation_id = convId;
    if (maxCitations !== undefined) body.max_citations = maxCitations;

    console.log("📤 Sending to backend:", { url: `${API_URL}/chat`, body });

    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }

    const data: ChatResponse = await response.json();
    return data.answer;
  }
  console.log(import.meta.env)
  console.warn("⚠️ API_URL not defined, using mock response. API_URL =", API_URL);
  return await mockResponse();
}


// Helpers
function generateUUID(): string {
  try {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
      // modern browsers
      // @ts-ignore
      return crypto.randomUUID();
    }
  } catch (e) {
    // ignore and fallback
  }

  // Fallback simple UUIDv4-ish generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getOrCreateConversationId(): string {
  const key = 'conversation_id';
  try {
    if (typeof localStorage !== 'undefined') {
      let id = localStorage.getItem(key);
      if (!id) {
        id = generateUUID();
        try {
          localStorage.setItem(key, id);
        } catch (e) {
          // ignore storage errors (e.g., quota)
        }
      }
      return id;
    }
  } catch (e) {
    // ignore and fallback
  }

  // Fallback if localStorage not available
  return generateUUID();
}

export function clearConversationId(): void {
  const key = 'conversation_id';
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(key);
    }
  } catch (e) {
    // ignore storage errors
  }
}
