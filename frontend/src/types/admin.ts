export interface AdminUser {
  id: string;
  email: string;
  role: string;
  doc_count: number;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  total_docs: number;
  total_messages: number;
  uploads_by_day: { date: string; count: number }[];
}