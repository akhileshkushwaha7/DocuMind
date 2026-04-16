export interface Document {
  id: string;
  filename: string;
  status: "pending" | "processing" | "ready" | "failed";
  created_at: string;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
}