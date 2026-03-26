import { create } from "zustand";

export type AppSection = "dashboard" | "documents" | "uploads" | "ai";

type UIState = {
  sidebarOpen: boolean;
  activeSection: AppSection;
  setSidebarOpen: (open: boolean) => void;
  setActiveSection: (section: AppSection) => void;
};

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  activeSection: "dashboard",
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  setActiveSection: (activeSection: AppSection) => set({ activeSection }),
}));
