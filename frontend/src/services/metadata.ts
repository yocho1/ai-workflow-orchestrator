import { ApiEnvelope, MetadataRecord } from "../types/api";
import { httpClient } from "./http";

type MetadataUpdatePayload = {
  document_type?: string;
  confidence_score?: number;
  extracted_data?: Record<string, unknown>;
};

export async function extractMetadata(documentId: number): Promise<MetadataRecord> {
  const response = await httpClient.post<ApiEnvelope<MetadataRecord>>(
    `/documents/${documentId}/extract-metadata`,
    {},
  );
  return response.data.data;
}

export async function getMetadata(documentId: number): Promise<MetadataRecord> {
  const response = await httpClient.get<MetadataRecord>(`/documents/${documentId}/metadata`);
  return response.data;
}

export async function updateMetadata(
  documentId: number,
  payload: MetadataUpdatePayload,
): Promise<MetadataRecord> {
  const response = await httpClient.patch<ApiEnvelope<MetadataRecord>>(
    `/documents/${documentId}/metadata`,
    payload,
  );
  return response.data.data;
}
