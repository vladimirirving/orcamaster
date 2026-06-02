import { useState } from 'react'
import * as Toast from '@radix-ui/react-toast'
import { useToastStore } from '@/hooks/useToast'

function ToastItem({ id, title, variant }: { id: string; title: string; variant: 'success' | 'error' }) {
  const [open, setOpen] = useState(true)
  const { remove } = useToastStore()

  return (
    <Toast.Root
      open={open}
      onOpenChange={(o) => {
        if (!o) {
          setOpen(false)
          remove(id)
        }
      }}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm
        ${variant === 'error' ? 'bg-red-800' : 'bg-gray-800'}`}
    >
      <Toast.Title className="font-medium">{title}</Toast.Title>
      <Toast.Action altText="fechar" asChild>
        <button onClick={() => { setOpen(false); remove(id) }} className="ml-auto text-gray-400 hover:text-white">✕</button>
      </Toast.Action>
    </Toast.Root>
  )
}

export default function Toaster() {
  const { toasts } = useToastStore()
  return (
    <Toast.Provider swipeDirection="right">
      {toasts.map(t => (
        <ToastItem key={t.id} id={t.id} title={t.title} variant={t.variant} />
      ))}
      <Toast.Viewport className="fixed bottom-4 right-4 flex flex-col gap-2 z-50 w-80" />
    </Toast.Provider>
  )
}
