export type ApiError = {
  message: string;
  details: unknown;
};

export type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  error: ApiError | null;
};

export type DocumentRecord = {
  id: number;
  filename: string;
  content_type: string;
  storage_path: string;
  extracted_text: string | null;
  processing_status: string;
  document_type: string | null;
  user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ClassificationResult = {
  document_id: number;
  document_type: string;
  confidence: number;
  reasoning: string;
};

export type AskDocumentResult = {
  document_id: number;
  question: string;
  answer: string;
  confidence: number | null;
  context_chunks_used: number;
};
