import { create } from "zustand";

const TOKEN_KEY = "workflow_auth_token";

type AuthUser = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: string;
};

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  isAuthReady: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  setUser: (user: AuthUser | null) => void;
  markAuthReady: () => void;
  logout: () => void;
};

function readInitialToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export const useAuthStore = create<AuthState>()((set) => ({
  token: readInitialToken(),
  user: null,
  isAuthReady: false,
  setAuth: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, user, isAuthReady: true });
  },
  setUser: (user) => set({ user }),
  markAuthReady: () => set({ isAuthReady: true }),
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, user: null, isAuthReady: true });
  },
}));
