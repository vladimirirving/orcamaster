import { create } from 'zustand'

interface ToastItem {
  id: string
  title: string
  variant: 'success' | 'error'
}

interface ToastState {
  toasts: ToastItem[]
  add: (title: string, variant?: 'success' | 'error') => void
  remove: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  add: (title, variant = 'success') => {
    const id = crypto.randomUUID()
    set((s) => ({ toasts: [...s.toasts, { id, title, variant }] }))
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) })), 3500)
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))

export const toast = (title: string, variant?: 'success' | 'error') =>
  useToastStore.getState().add(title, variant)
