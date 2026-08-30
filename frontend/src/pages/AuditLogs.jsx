import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../Layout'
import { api } from '../api'

export default function AuditLogs() {
  const [log, setLog] = useState([])
  const [verifyResult, setVerifyResult] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      setLog(await api.auditLog()) // no case filter - every action across every case
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleVerifyChain() {
    setError(null)
    try {
      setVerifyResult(await api.auditVerify())
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <Layout headerLeft={<div><p className="text-xs text-slate-400">Security</p><p className="text-sm font-medium text-slate-900">Audit Logs</p></div>}>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-xl font-semibold text-slate-900">Audit Logs</h1>
          <button
            onClick={handleVerifyChain}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 hover:bg-slate-50"
          >
            Verify chain integrity
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-6">
          Every action recorded across every case, in a hash-chained, tamper-evident ledger.
        </p>

        {verifyResult && (
          <div className={`rounded-md p-3 text-sm mb-4 ${verifyResult.valid ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800 font-semibold'}`}>
            {verifyResult.valid
              ? `Chain intact - ${verifyResult.entries_checked} entries verified.`
              : `TAMPERING DETECTED at entry #${verifyResult.broken_at_id}: ${verifyResult.reason}`}
          </div>
        )}
        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
          {log.length === 0 && <p className="p-8 text-sm text-slate-500 text-center">No actions recorded yet.</p>}
          {log.map((entry) => (
            <button
              key={entry.id}
              onClick={() => entry.case_id && navigate(`/cases/${encodeURIComponent(entry.case_id)}`)}
              className="w-full text-left p-3 text-sm flex items-center justify-between hover:bg-slate-50"
            >
              <div>
                <span className="font-medium text-slate-900">{entry.action}</span>
                <span className="text-slate-500"> by {entry.actor}</span>
                {entry.case_id && <span className="text-slate-400"> · case {entry.case_id}</span>}
                {entry.details && <span className="text-slate-400"> — {entry.details}</span>}
              </div>
              <span className="text-xs text-slate-400 shrink-0">{new Date(entry.timestamp).toLocaleString()}</span>
            </button>
          ))}
        </div>
      </div>
    </Layout>
  )
}
