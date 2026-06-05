import { useState, useRef, useEffect } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import PerfilModal from '@/components/layout/PerfilModal'

const CADASTROS_ITEMS = [
  {
    label: 'Clientes',
    to: '/clientes',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
  {
    label: 'Fornecedores',
    to: '/fornecedores',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"/>
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
      </svg>
    ),
  },
  {
    label: 'Insumos',
    to: '/insumos',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
    ),
  },
]

export default function TopBar() {
  const { logout, papel, nome } = useAuth()
  const navigate = useNavigate()
  const [userDropdown, setUserDropdown] = useState(false)
  const [cadastrosDropdown, setCadastrosDropdown] = useState(false)
  const [perfilOpen, setPerfilOpen] = useState(false)
  const userRef = useRef<HTMLDivElement>(null)
  const cadastrosRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserDropdown(false)
      if (cadastrosRef.current && !cadastrosRef.current.contains(e.target as Node)) setCadastrosDropdown(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function handleLogout() {
    setUserDropdown(false)
    try { await logout() } finally { navigate('/login') }
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `hover:text-blue-300 transition-colors text-sm ${isActive ? 'text-blue-400 font-medium' : ''}`

  return (
    <header className="bg-gray-900 text-white px-4 h-12 flex items-center gap-6 shrink-0">
      <span className="font-bold text-blue-400">AVML</span>
      <nav className="flex gap-4 text-sm items-center">
        <NavLink to="/" end className={navLinkClass}>Dashboard</NavLink>
        <NavLink to="/obras" className={navLinkClass}>Obras</NavLink>

        {/* Dropdown Cadastros */}
        <div className="relative" ref={cadastrosRef}>
          <button
            onClick={() => setCadastrosDropdown(v => !v)}
            className="flex items-center gap-1 text-sm hover:text-blue-300 transition-colors"
          >
            Cadastros
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-gray-500 mt-0.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {cadastrosDropdown && (
            <div className="absolute top-8 left-0 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-44 z-50 border border-gray-100">
              {CADASTROS_ITEMS.map(item => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setCadastrosDropdown(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-sm hover:bg-gray-50 text-gray-700"
                >
                  <span className="text-gray-400">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>
          )}
        </div>

        <NavLink to="/composicoes" className={navLinkClass}>Base de Comp.</NavLink>
        <NavLink to="/relatorios" className={navLinkClass}>Relatórios</NavLink>
      </nav>

      <div className="ml-auto flex items-center gap-3 text-sm">
        {papel === 'admin' && (
          <Link to="/configuracoes" className="text-gray-400 hover:text-white transition-colors text-sm">
            Configurações
          </Link>
        )}
        <div className="relative" ref={userRef}>
          <button
            onClick={() => setUserDropdown(v => !v)}
            className="text-gray-300 hover:text-white transition-colors flex items-center gap-1"
          >
            {nome ?? papel}
            <span className="text-gray-500 text-xs">▾</span>
          </button>
          {userDropdown && (
            <div className="absolute right-0 top-8 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-36 z-50">
              <button
                onClick={() => { setUserDropdown(false); setPerfilOpen(true) }}
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
