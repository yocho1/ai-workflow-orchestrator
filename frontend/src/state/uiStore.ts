import { create } from "zustand";

type UIState = {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
}));
