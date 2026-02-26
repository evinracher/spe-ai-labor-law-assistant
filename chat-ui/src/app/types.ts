export interface Citation {
  source: string;
  page: number | null;
  chunk_id: string | null;
  snippet: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "typing" | "error";
  text: string;
  ts: string;
  citations?: Citation[];
}
