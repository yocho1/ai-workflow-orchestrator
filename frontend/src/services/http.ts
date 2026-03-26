import axios, { AxiosError } from "axios";

import { getStoredToken } from "../state/authStore";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const httpClient = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getHttpErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const axiosError = error as AxiosError<{ detail?: string; message?: string; error?: { message?: string } }>;

  if (axiosError.code === "ERR_NETWORK") {
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      return "No internet connection. Reconnect and try again.";
    }
    return "Network error. Check that frontend and backend are running.";
  }

  if (axiosError.code === "ECONNABORTED") {
    return "Request timed out. Please retry.";
  }

  const apiMessage =
    axiosError.response?.data?.error?.message ??
    axiosError.response?.data?.detail ??
    axiosError.response?.data?.message;
  if (apiMessage) {
    return apiMessage;
  }

  if (axiosError.response?.status) {
    return `${fallback} (HTTP ${axiosError.response.status}).`;
  }

  return fallback;
}
