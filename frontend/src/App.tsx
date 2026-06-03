import { type ReactNode } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ObrasPage from '@/pages/ObrasPage'
import ObraDetailPage from '@/pages/ObraDetailPage'
import PlanilhaPage from '@/pages/PlanilhaPage'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import TopBar from '@/components/layout/TopBar'
import Toaster from '@/components/layout/Toaster'
import EmpresaSettingsPage from '@/pages/EmpresaSettingsPage'

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <TopBar />
      <main className="flex-1 overflow-auto">{children}</main>
      <Toaster />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/obras" element={<ObrasPage />} />
                <Route path="/obras/:id" element={<ObraDetailPage />} />
                <Route path="/obras/:obraId/versoes/:versaoId" element={<PlanilhaPage />} />
                <Route path="/configuracoes" element={<EmpresaSettingsPage />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
