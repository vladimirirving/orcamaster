import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import PerfilModal from '@/components/layout/PerfilModal'

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Obras', to: '/obras' },
  { label: 'Orçamento', to: '/orcamento' },
  { label: 'BDI', to: '/bdi' },
  { label: 'Cronograma', to: '/cronograma' },
  { label: 'Medição', to: '/medicao' },
  { label: 'Relatórios', to: '/relatorios' },
  { label: 'Base de Comp.', to: '/composicoes' },
]

export default function TopBar() {
  const { logout, papel, nome } = useAuth()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [perfilOpen, setPerfilOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function handleLogout() {
    setDropdownOpen(false)
    try {
      await logout()
    } finally {
      navigate('/login')
    }
  }

  return (
    <header className="bg-gray-900 text-white px-4 h-12 flex items-center gap-6 shrink-0">
      <span className="font-bold text-blue-400">AVML</span>
      <nav className="flex gap-4 text-sm">
        {NAV_ITEMS.map(item => (
          <Link key={item.to} to={item.to} className="hover:text-blue-300 transition-colors">
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3 text-sm">
        {papel === 'admin' && (
          <Link to="/configuracoes" className="text-gray-400 hover:text-white transition-colors">
            Configurações
          </Link>
        )}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(v => !v)}
            className="text-gray-300 hover:text-white transition-colors flex items-center gap-1"
          >
            {nome ?? papel}
            <span className="text-gray-500 text-xs">▾</span>
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 top-8 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-36 z-50">
              <button
                onClick={() => { setDropdownOpen(false); setPerfilOpen(true) }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
              >
                Meu Perfil
              </button>
              <hr className="border-gray-100 my-1" />
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
      {perfilOpen && <PerfilModal onClose={() => setPerfilOpen(false)} />}
    </header>
  )
}
