import { ApiEnvelope, JobStatusResponse } from "../types/api";
import { httpClient } from "./http";

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await httpClient.get<ApiEnvelope<JobStatusResponse>>(`/jobs/${jobId}`);
  return response.data.data;
}
