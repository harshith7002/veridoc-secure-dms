import { useState, useEffect, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import Layout from '../Layout'
import { api } from '../api'

const DOCUMENT_TYPES = [
  'FIR', 'INVESTIGATION_RECORD', 'WITNESS_STATEMENT', 'CHARGE_SHEET',
  'COURT_FILING', 'EVIDENCE_RECORD', 'FORENSIC_REPORT', 'LEGAL_NOTICE',
]

const STATUSES = ['OPEN', 'UNDER_INVESTIGATION', 'PENDING_REVIEW', 'CLOSED']

const TABS = ['Documents', 'Search', 'Audit trail']

export default function CaseDetail() {
  const { caseNumber } = useParams()
  const [tab, setTab] = useState('Documents')
  const [caseInfo, setCaseInfo] = useState(null)
  const [error, setError] = useState(null)

  const loadCase = useCallback(async () => {
    try {
      setCaseInfo(await api.getCase(caseNumber))
    } catch (err) {
      setError(err.message)
    }
  }, [caseNumber])

  useEffect(() => {
    loadCase()
  }, [loadCase])

  async function handleStatusChange(e) {
    try {
      setCaseInfo(await api.updateCaseStatus(caseNumber, e.target.value))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <Layout headerLeft={<div><p className="text-xs text-slate-400">Cases</p><p className="text-sm font-medium text-slate-900">{caseNumber}</p></div>}>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <Link to="/" className="text-sm text-slate-500 hover:text-slate-900 mb-4 inline-block">
          ← Back to dashboard
        </Link>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              {caseNumber} {caseInfo && <span className="text-slate-500 font-normal">· {caseInfo.title}</span>}
            </h2>
            {caseInfo && (
              <p className="text-sm text-slate-500">
                {caseInfo.priority} priority · opened by {caseInfo.created_by}
              </p>
            )}
          </div>
          {caseInfo && (
            <select
              value={caseInfo.status}
              onChange={handleStatusChange}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s.replaceAll('_', ' ')}</option>
              ))}
            </select>
          )}
        </div>
        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <div className="border-b border-slate-200 mb-6">
          <nav className="flex gap-6">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`pb-3 text-sm font-medium border-b-2 -mb-px ${
                  tab === t ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>

        {tab === 'Documents' && <DocumentsPanel caseId={caseNumber} />}
        {tab === 'Search' && <SearchPanel caseId={caseNumber} />}
        {tab === 'Audit trail' && <AuditPanel caseId={caseNumber} />}
      </div>
    </Layout>
  )
}

function DocumentsPanel({ caseId }) {
  const [documents, setDocuments] = useState([])
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0])
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [integrityResults, setIntegrityResults] = useState({})

  const loadDocuments = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments(caseId))
    } catch (err) {
      setError(err.message)
    }
  }, [caseId])

  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      const text = await file.text()
      const doc = await api.uploadDocument(caseId, documentType, file)
      // best-effort: also index for semantic search. If this fails, the upload itself
      // already succeeded and was audit-logged - search indexing is not load-bearing.
      try {
        await api.indexForSearch(doc.id, caseId, documentType, text)
      } catch {
        // non-fatal
      }
      setFile(null)
      await loadDocuments()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleDownload(doc) {
    const blob = await api.downloadDocument(doc.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = doc.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleVerify(doc) {
    const result = await api.verifyDocumentIntegrity(doc.id)
    setIntegrityResults((prev) => ({ ...prev, [doc.id]: result }))
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleUpload} className="bg-white border border-slate-200 rounded-lg p-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Document type</label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t} value={t}>{t.replaceAll('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">File</label>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} className="text-sm" />
        </div>
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-md bg-slate-900 text-white text-sm font-medium px-4 py-1.5 hover:bg-slate-800 disabled:opacity-50"
        >
          {busy ? 'Uploading...' : 'Upload (encrypted at rest)'}
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        {documents.length === 0 && <p className="p-4 text-sm text-slate-500">No documents for this case yet.</p>}
        {documents.map((doc) => (
          <div key={doc.id} className="p-4 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{doc.filename}</p>
              <p className="text-xs text-slate-500">
                {doc.document_type.replaceAll('_', ' ')} · uploaded by {doc.uploaded_by} · sha256 {doc.sha256_hash.slice(0, 16)}...
              </p>
              {integrityResults[doc.id] && (
                <p className={`text-xs mt-1 ${integrityResults[doc.id].intact ? 'text-green-700' : 'text-red-600 font-semibold'}`}>
                  {integrityResults[doc.id].intact ? 'Integrity check passed' : 'INTEGRITY CHECK FAILED — possible tampering'}
                </p>
              )}
            </div>
            <div className="flex gap-2 shrink-0">
              <button onClick={() => handleVerify(doc)} className="text-xs px-3 py-1.5 rounded-md border border-slate-300 hover:bg-slate-50">
                Verify integrity
              </button>
              <button onClick={() => handleDownload(doc)} className="text-xs px-3 py-1.5 rounded-md border border-slate-300 hover:bg-slate-50">
                Download
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function SearchPanel({ caseId }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSearch(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const res = await api.search(query, caseId)
      setResults(res.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search across documents in this case (semantic - try describing an idea, not just keywords)"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
        <button
          type="submit"
          disabled={!query || busy}
          className="rounded-md bg-slate-900 text-white text-sm font-medium px-4 py-2 hover:bg-slate-800 disabled:opacity-50"
        >
          {busy ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {results && (
        <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
          {results.length === 0 && <p className="p-4 text-sm text-slate-500">No matches.</p>}
          {results.map((r) => (
            <div key={r.chunk_id} className="p-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-500">
                  doc #{r.document_id} · {r.document_type?.replaceAll('_', ' ')}
                </span>
                <span className="text-xs text-slate-400">score {r.score.toFixed(3)}</span>
              </div>
              <p className="text-sm text-slate-800">{r.chunk_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AuditPanel({ caseId }) {
  const [log, setLog] = useState([])
  const [verifyResult, setVerifyResult] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      setLog(await api.auditLog(caseId))
    } catch (err) {
      setError(err.message)
    }
  }, [caseId])

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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-slate-700">Action history for {caseId}</h2>
        <button
          onClick={handleVerifyChain}
          className="text-sm px-3 py-1.5 rounded-md border border-slate-300 hover:bg-slate-50"
        >
          Verify chain integrity
        </button>
      </div>

      {verifyResult && (
        <div className={`rounded-md p-3 text-sm ${verifyResult.valid ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800 font-semibold'}`}>
          {verifyResult.valid
            ? `Chain intact - ${verifyResult.entries_checked} entries verified.`
            : `TAMPERING DETECTED at entry #${verifyResult.broken_at_id}: ${verifyResult.reason}`}
        </div>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
        {log.length === 0 && <p className="p-4 text-sm text-slate-500">No actions recorded for this case yet.</p>}
        {log.map((entry) => (
          <div key={entry.id} className="p-3 text-sm flex items-center justify-between">
            <div>
              <span className="font-medium text-slate-900">{entry.action}</span>
              <span className="text-slate-500"> by {entry.actor}</span>
              {entry.details && <span className="text-slate-400"> — {entry.details}</span>}
            </div>
            <span className="text-xs text-slate-400">{new Date(entry.timestamp).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
