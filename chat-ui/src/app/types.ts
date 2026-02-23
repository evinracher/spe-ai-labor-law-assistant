export interface Message {
  id: string;
  role: "user" | "assistant" | "typing" | "error";
  text: string;
  ts: string;
}
