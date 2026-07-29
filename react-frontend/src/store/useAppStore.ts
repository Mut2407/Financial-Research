import { create } from 'zustand';

interface AppState {
  isAuthenticated: boolean;
  username: string | null;
  datasetCount: number;
  login: (username: string) => void;
  logout: () => void;
  setDatasetCount: (count: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  isAuthenticated: false,
  username: null,
  datasetCount: 0,
  login: (username) => set({ isAuthenticated: true, username }),
  logout: () => set({ isAuthenticated: false, username: null }),
  setDatasetCount: (count) => set({ datasetCount: count }),
}));
