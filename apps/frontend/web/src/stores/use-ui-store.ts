import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  activeChatId: string | null
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setActiveChatId: (chatId: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeChatId: null,
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open: boolean) =>
    set({ sidebarOpen: open }),
  setActiveChatId: (chatId: string | null) =>
    set({ activeChatId: chatId }),
}))