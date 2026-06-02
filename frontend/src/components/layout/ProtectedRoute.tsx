import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { userId, refresh } = useAuth()
  const [checking, setChecking] = useState(!userId)

  useEffect(() => {
    if (!userId) {
      refresh().finally(() => setChecking(false))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (checking) return <div className="min-h-screen flex items-center justify-center">Carregando...</div>
  if (!userId) return <Navigate to="/login" replace />
  return <>{children}</>
}
