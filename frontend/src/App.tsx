import { type ReactNode } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ObrasPage from '@/pages/ObrasPage'
import ObraDetailPage from '@/pages/ObraDetailPage'
import PlanilhaPage from '@/pages/PlanilhaPage'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import Sidebar from '@/components/layout/Sidebar'
import Toaster from '@/components/layout/Toaster'
import EmpresaSettingsPage from '@/pages/EmpresaSettingsPage'
import RelatoriosPage from '@/pages/RelatoriosPage'
import ComposicoesPage from '@/pages/ComposicoesPage'
import ClientesPage from '@/pages/ClientesPage'
import ClienteDetailPage from '@/pages/ClienteDetailPage'
import FornecedoresPage from '@/pages/FornecedoresPage'
import FornecedorDetailPage from '@/pages/FornecedorDetailPage'
import DiarioObraPage from '@/pages/DiarioObraPage'
import InsumosPage from '@/pages/InsumosPage'

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex bg-gray-100">
      <Sidebar />
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
                <Route path="/composicoes" element={<ComposicoesPage />} />
                <Route path="/relatorios" element={<RelatoriosPage />} />
                <Route path="/clientes" element={<ClientesPage />} />
                <Route path="/clientes/:id" element={<ClienteDetailPage />} />
                <Route path="/fornecedores" element={<FornecedoresPage />} />
                <Route path="/fornecedores/:id" element={<FornecedorDetailPage />} />
                <Route path="/obras/:obraId/diario" element={<DiarioObraPage />} />
                <Route path="/insumos" element={<InsumosPage />} />
                <Route path="*" element={
                  <div className="p-10 text-center text-gray-400 text-sm">Página não encontrada.</div>
                } />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
