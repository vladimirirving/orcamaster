import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import TopBar from '@/components/layout/TopBar'

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <TopBar />
      <main className="flex-1 overflow-auto">{children}</main>
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
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
