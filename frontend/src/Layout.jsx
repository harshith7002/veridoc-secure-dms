import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ShieldCheck, LayoutDashboard, FolderOpen, FilePlus2, FileText, Search, ScrollText } from 'lucide-react'
import { useAuth } from './AuthContext'

const NAV_SECTIONS = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', to: '/', icon: LayoutDashboard },
      { label: 'Cases', to: '/', icon: FolderOpen },
    ],
  },
  {
    label: 'Documents',
    items: [
      { label: 'Document Repository', to: '/documents', icon: FileText },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'AI Semantic Search', to: '/search', icon: Search },
    ],
  },
  {
    label: 'Security',
    items: [
      { label: 'Audit Logs', to: '/audit', icon: ScrollText },
    ],
  },
]

export default function Layout({ children, headerLeft, headerRight }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState('')

  function handleGlobalSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-60 shrink-0 bg-slate-950 text-slate-300 flex flex-col">
        <div className="px-5 py-5 flex items-center gap-2 border-b border-slate-800">
          <ShieldCheck size={22} className="text-emerald-400" />
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Solvexa</p>
            <p className="text-sm font-medium text-white leading-tight">Secure Case Management</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="mb-5">
              <p className="px-5 text-[11px] font-semibold tracking-wide text-slate-500 uppercase mb-1">
                {section.label}
              </p>
              {section.items.map((item) => {
                const active = location.pathname === item.to
                const Icon = item.icon
                return (
                  <button
                    key={item.label}
                    onClick={() => navigate(item.to)}
                    className={`w-full flex items-center gap-2.5 px-5 py-2 text-sm text-left ${
                      active ? 'bg-slate-800 text-white border-l-2 border-emerald-400' : 'text-slate-300 hover:bg-slate-900 hover:text-white border-l-2 border-transparent'
                    }`}
                  >
                    <Icon size={16} />
                    {item.label}
                  </button>
                )
              })}
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4">
          <div className="flex-1">{headerLeft}</div>
          <form onSubmit={handleGlobalSearch} className="w-72">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Global search"
                className="w-full rounded-md border border-slate-300 pl-8 pr-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
          </form>
          <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1">
            <ShieldCheck size={13} />
            Session active · RBAC enforced
          </span>
          {headerRight}
          {user && (
            <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-slate-900 text-white text-xs font-medium flex items-center justify-center">
                {user.email.slice(0, 2).toUpperCase()}
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-slate-900 leading-tight">{user.email.split('@')[0]}</p>
                <p className="text-[11px] text-slate-500 leading-tight">{user.role.replaceAll('_', ' ')}</p>
              </div>
              <button onClick={logout} className="ml-2 text-xs text-slate-500 hover:text-slate-900">
                Sign out
              </button>
            </div>
          )}
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  )
}
