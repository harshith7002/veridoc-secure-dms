import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, ShieldCheck, AlertTriangle, Activity, Inbox } from 'lucide-react'
import Layout from '../Layout'
import { api } from '../api'
import { useAuth } from '../AuthContext'

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH']

export default function DashboardHome() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [cases, setCases] = useState([])
  const [auditLog, setAuditLog] = useState([])
  const [error, setError] = useState(null)
  const [showNewCase, setShowNewCase] = useState(false)
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      const [statsRes, casesRes, auditRes] = await Promise.all([
        api.caseStats(),
        api.listCases(),
        api.auditLog().catch(() => []), // recent activity is a nice-to-have, don't block the page on it
      ])
      setStats(statsRes)
      setCases(casesRes)
      setAuditLog(auditRes.slice(-5).reverse())
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const firstName = user?.email.split('@')[0].split('.')[0]
  const displayName = firstName ? firstName[0].toUpperCase() + firstName.slice(1) : ''

  const cards = [
    { label: 'Total cases', value: stats?.total_cases, sub: 'Accessible to your session', icon: FolderOpen, tone: 'slate' },
    { label: 'Active cases', value: stats?.active_cases, sub: 'Open and under investigation', icon: ShieldCheck, tone: 'blue' },
    { label: 'Pending review', value: stats?.pending_review, sub: 'Awaiting next action', icon: AlertTriangle, tone: 'amber' },
    { label: 'High priority', value: stats?.high_priority, sub: 'Requires immediate attention', icon: Activity, tone: 'red' },
  ]

  const toneClasses = {
    slate: 'bg-slate-100 text-slate-600',
    blue: 'bg-blue-100 text-blue-600',
    amber: 'bg-amber-100 text-amber-600',
    red: 'bg-red-100 text-red-600',
  }

  return (
    <Layout headerLeft={<div><p className="text-xs text-slate-400">Dashboard</p><p className="text-sm font-medium text-slate-900">Command center for authorized case work.</p></div>}>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs font-semibold tracking-wide text-emerald-700 uppercase mb-1">Secure operations</p>
            <h1 className="text-2xl font-semibold text-slate-900">Good morning, {displayName}</h1>
            <p className="text-sm text-slate-500 mt-1">
              Here's an overview of your accessible case management activity. Your current role: {user?.role.replaceAll('_', ' ')}.
            </p>
          </div>
          <button
            onClick={() => setShowNewCase(true)}
            className="rounded-md bg-slate-900 text-white text-sm font-medium px-4 py-2 hover:bg-slate-800 shrink-0"
          >
            + New case
          </button>
        </div>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <div className="grid grid-cols-4 gap-4 mb-8">
          {cards.map((c) => {
            const Icon = c.icon
            return (
              <div key={c.label} className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-medium text-slate-500">{c.label.toUpperCase()}</p>
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center ${toneClasses[c.tone]}`}>
                    <Icon size={14} />
                  </span>
                </div>
                <p className="text-3xl font-semibold text-slate-900">{c.value ?? '—'}</p>
                <p className="text-xs text-slate-400 mt-1">{c.sub}</p>
              </div>
            )
          })}
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-medium text-slate-900">Recent cases</h3>
              <p className="text-xs text-slate-400">Ordered by update activity</p>
            </div>
            {cases.length === 0 ? (
              <EmptyState onCreate={() => setShowNewCase(true)} />
            ) : (
              <div className="divide-y divide-slate-100">
                {cases.slice(0, 5).map((c) => (
                  <button
                    key={c.id}
                    onClick={() => navigate(`/cases/${encodeURIComponent(c.case_number)}`)}
                    className="w-full text-left p-4 hover:bg-slate-50"
                  >
                    <p className="text-sm font-medium text-slate-900">{c.case_number} · {c.title}</p>
                    <p className="text-xs text-slate-500">{c.status.replaceAll('_', ' ')} · {c.priority} priority</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="px-4 py-3 border-b border-slate-100">
              <h3 className="text-sm font-medium text-slate-900">Recent activity</h3>
              <p className="text-xs text-slate-400">Latest actions across your accessible cases</p>
            </div>
            {auditLog.length === 0 ? (
              <div className="p-8 text-center">
                <Inbox size={28} className="mx-auto text-slate-300 mb-2" />
                <p className="text-sm text-slate-500">No activity yet.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {auditLog.map((entry) => (
                  <div key={entry.id} className="p-3 text-sm">
                    <span className="font-medium text-slate-900">{entry.action}</span>
                    <span className="text-slate-500"> by {entry.actor}</span>
                    {entry.case_id && <span className="text-slate-400"> · {entry.case_id}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {showNewCase && (
        <NewCaseModal
          onClose={() => setShowNewCase(false)}
          onCreated={(caseNumber) => {
            setShowNewCase(false)
            navigate(`/cases/${encodeURIComponent(caseNumber)}`)
          }}
        />
      )}
    </Layout>
  )
}

function EmptyState({ onCreate }) {
  return (
    <div className="p-8 text-center">
      <FolderOpen size={28} className="mx-auto text-slate-300 mb-2" />
      <p className="text-sm text-slate-500 mb-4">No cases available. Create your first one to get started.</p>
      <button
        onClick={onCreate}
        className="rounded-md bg-slate-900 text-white text-sm font-medium px-4 py-2 hover:bg-slate-800"
      >
        Create your first case
      </button>
    </div>
  )
}

function NewCaseModal({ onClose, onCreated }) {
  const [caseNumber, setCaseNumber] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('MEDIUM')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await api.createCase(caseNumber, title, description || null, priority)
      onCreated(caseNumber)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-10">
      <div className="w-full max-w-md bg-white rounded-xl p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">New case</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Case number</label>
            <input
              required
              value={caseNumber}
              onChange={(e) => setCaseNumber(e.target.value)}
              placeholder="CASE-8891"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="text-sm px-4 py-2 rounded-md border border-slate-300 hover:bg-slate-50">
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy}
              className="text-sm px-4 py-2 rounded-md bg-slate-900 text-white font-medium hover:bg-slate-800 disabled:opacity-50"
            >
              {busy ? 'Creating...' : 'Create case'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
