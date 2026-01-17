export interface Citation {
  doc_id: string;
  element_id: string;
  page_number: number;
  bbox: number[];
  snippet: string;
  crop_uri?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  session_id: string;
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  status: string;
  expires_at?: string;
}
