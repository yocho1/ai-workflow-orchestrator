import { httpClient } from "./http";
import { ApiEnvelope } from "../types/api";

type AuthUser = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: string;
};

type AuthPayload = {
  token: {
    access_token: string;
    token_type: string;
    expires_in: number;
  };
  user: AuthUser;
};

export async function register(email: string, fullName: string, password: string): Promise<AuthPayload> {
  const response = await httpClient.post<ApiEnvelope<AuthPayload>>("/auth/register", {
    email,
    full_name: fullName,
    password,
  });
  return response.data.data;
}

export async function login(email: string, password: string): Promise<AuthPayload> {
  const response = await httpClient.post<ApiEnvelope<AuthPayload>>("/auth/login", {
    email,
    password,
  });
  return response.data.data;
}

export async function me(): Promise<AuthUser> {
  const response = await httpClient.get<ApiEnvelope<AuthUser>>("/auth/me");
  return response.data.data;
}
