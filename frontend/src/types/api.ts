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

export type MetadataRecord = {
  id: number;
  document_id: number;
  document_type: string;
  confidence_score: number;
  extracted_data: Record<string, unknown>;
  extraction_model: string;
  extraction_error: string | null;
  created_at: string;
  updated_at: string;
};

export type MetadataReviewQueueItem = {
  document_id: number;
  filename: string;
  document_type: string;
  confidence_score: number;
  review_reason: string | null;
  updated_at: string;
};

export type BatchExtractStartResponse = {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_documents: number;
};

export type JobStatusResponse = {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_documents: number;
  processed_documents: number;
  success_count: number;
  failure_count: number;
  progress_percent: number;
  started_at: string;
  finished_at: string | null;
  error: string | null;
};
