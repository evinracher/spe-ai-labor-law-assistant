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
  if (API_URL) {
    const body: ChatRequest = { question };
    if (conversationId) body.conversation_id = conversationId;
    if (maxCitations !== undefined) body.max_citations = maxCitations;

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

  return await mockResponse();
}
