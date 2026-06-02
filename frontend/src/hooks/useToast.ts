import { create } from 'zustand'

interface ToastItem {
  id: string
  title: string
  variant: 'success' | 'error'
  timerId: ReturnType<typeof setTimeout>
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
    const timerId = setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) }))
    }, 3500)
    set((s) => ({ toasts: [...s.toasts, { id, title, variant, timerId }] }))
  },
  remove: (id) => set((s) => {
    const toast = s.toasts.find(t => t.id === id)
    if (toast) clearTimeout(toast.timerId)
    return { toasts: s.toasts.filter(t => t.id !== id) }
  }),
}))

export const toast = (title: string, variant?: 'success' | 'error') =>
  useToastStore.getState().add(title, variant)
