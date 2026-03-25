import { httpClient } from "./http";
import { ApiEnvelope, DocumentRecord } from "../types/api";

type CreateDocumentPayload = {
  filename: string;
  extracted_text: string;
};

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await httpClient.get<ApiEnvelope<DocumentRecord[]>>("/documents");
  return response.data.data;
}

export async function createDocument(payload: CreateDocumentPayload): Promise<DocumentRecord> {
  const response = await httpClient.post<ApiEnvelope<DocumentRecord>>("/documents", {
    filename: payload.filename,
    content_type: "text/plain",
    storage_path: `/uploads/${payload.filename}`,
    extracted_text: payload.extracted_text,
  });
  return response.data.data;
}
