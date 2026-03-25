import { httpClient } from "./http";
import { ApiEnvelope, AskDocumentResult, ClassificationResult } from "../types/api";

export async function classifyDocument(documentId: number): Promise<ClassificationResult> {
  const response = await httpClient.post<ApiEnvelope<ClassificationResult>>(`/ai/documents/${documentId}/classify`, {});
  return response.data.data;
}

export async function askDocument(documentId: number, question: string): Promise<AskDocumentResult> {
  const response = await httpClient.post<ApiEnvelope<AskDocumentResult>>(`/ai/documents/${documentId}/ask`, { question });
  return response.data.data;
}
