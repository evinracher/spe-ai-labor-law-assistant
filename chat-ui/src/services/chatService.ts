import { mockResponse } from "../mocks/mockService";
import type { Citation, Trace, WorkflowTrace } from "../app/types";

interface ChatResponse {
  ok: boolean;
  request_id: string;
  answer: string;
  citations: Citation[];
  trace: Trace;
  workflow_trace?: WorkflowTrace;
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
): Promise<{ answer: string; citations?: Citation[]; trace?: Trace; workflow_trace?: WorkflowTrace }> {
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
    return {
      answer: data.answer,
      citations: data.citations,
      trace: data.trace,
      workflow_trace: data.workflow_trace
    };
  }
  
  return { answer: await mockResponse() };
}

function generateUUID(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  // Fallback simple UUIDv4-ish generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replaceAll(/[xy]/g, function (c) {
    const r = Math.trunc(Math.random() * 16);
    const v = c === 'x' ? r : (r % 4) + 8;
    return v.toString(16);
  });
}

export function getOrCreateConversationId(): string {
  const key = 'conversation_id';
  try {
    if (typeof localStorage !== 'undefined') {
      let id = localStorage.getItem(key);
      if (!id) {
        id = generateUUID();
        localStorage.setItem(key, id);
      }
      return id;
    }
  } catch {
    // ignore and fallback
  }
  
  return generateUUID();
}
