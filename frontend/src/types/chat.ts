export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface StreamMessage {
  token?: string;
  done?: boolean;
  error?: string;
}