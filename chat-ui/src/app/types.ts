export interface Citation {
  source: string;
  page: number | null;
  chunk_id: string | null;
  snippet: string;
}

export interface ToolTraceStep {
  tool_name: string;
  status: "success" | "failure" | "skipped";
  input?: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  timestamp?: string;
  duration_ms?: number;
}

export interface ValidationDetails {
  is_valid: boolean;
  coherence_score: number;
  grounding_score: number;
  hallucination_detected: boolean;
  completeness_score: number;
  reason?: string;
}

export interface WorkflowTrace {
  conversation_id: string;
  total_steps: number;
  tools_used: string[];
  tool_traces: ToolTraceStep[];
  validation_passed: boolean;
  validation_details?: ValidationDetails;
  execution_time_ms?: number;
  intent?: string;
}

export interface Trace {
  intent: string | null;
  top_k: number | null;
  vector_db: string;
  llm_provider: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "typing" | "error";
  text: string;
  ts: string;
  citations?: Citation[];
  trace?: Trace;
  workflow_trace?: WorkflowTrace;
}
