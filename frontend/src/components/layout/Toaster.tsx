import * as Toast from '@radix-ui/react-toast'
import { useToastStore } from '@/hooks/useToast'

export default function Toaster() {
  const { toasts, remove } = useToastStore()
  return (
    <Toast.Provider swipeDirection="right">
      {toasts.map(t => (
        <Toast.Root
          key={t.id}
          open
          onOpenChange={() => remove(t.id)}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm
            ${t.variant === 'error' ? 'bg-red-800' : 'bg-gray-800'}`}
        >
          <Toast.Title className="font-medium">{t.title}</Toast.Title>
          <Toast.Action altText="fechar" asChild>
            <button onClick={() => remove(t.id)} className="ml-auto text-gray-400 hover:text-white">✕</button>
          </Toast.Action>
        </Toast.Root>
      ))}
      <Toast.Viewport className="fixed bottom-4 right-4 flex flex-col gap-2 z-50 w-80" />
    </Toast.Provider>
  )
}
