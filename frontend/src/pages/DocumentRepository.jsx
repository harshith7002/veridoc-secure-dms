import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../Layout'
import { api } from '../api'

export default function DocumentRepository() {
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState(null)
  const [integrityResults, setIntegrityResults] = useState({})
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments())
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

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
    <Layout headerLeft={<div><p className="text-xs text-slate-400">Documents</p><p className="text-sm font-medium text-slate-900">Document Repository</p></div>}>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-slate-900 mb-1">Document Repository</h1>
        <p className="text-sm text-slate-500 mb-6">Every document accessible to your session, across all cases.</p>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
          {documents.length === 0 && (
            <p className="p-8 text-sm text-slate-500 text-center">No documents accessible to your session yet.</p>
          )}
          {documents.map((doc) => (
            <div key={doc.id} className="p-4 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <button
                  onClick={() => navigate(`/cases/${encodeURIComponent(doc.case_id)}`)}
                  className="text-sm font-medium text-slate-900 hover:underline truncate block text-left"
                >
                  {doc.filename}
                </button>
                <p className="text-xs text-slate-500">
                  {doc.document_type.replaceAll('_', ' ')} · case {doc.case_id} · uploaded by {doc.uploaded_by} · sha256 {doc.sha256_hash.slice(0, 16)}...
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
    </Layout>
  )
}
