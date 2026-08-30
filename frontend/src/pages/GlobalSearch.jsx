import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Layout from '../Layout'
import { api } from '../api'

export default function GlobalSearch() {
  const [searchParams] = useSearchParams()
  const urlQuery = searchParams.get('q') || ''
  const [query, setQuery] = useState(urlQuery)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  const runSearch = useCallback(async (q) => {
    if (!q.trim()) return
    setError(null)
    setBusy(true)
    try {
      const res = await api.search(q) // no case filter - searches across every case
      setResults(res.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }, [])

  // Re-runs whenever the URL's ?q= actually changes - not just on first mount - so the
  // top bar's global search (which navigates to /search?q=...) works even when you're
  // already sitting on this page, not just when arriving from elsewhere.
  useEffect(() => {
    if (urlQuery) {
      setQuery(urlQuery)
      runSearch(urlQuery)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlQuery])

  function handleSubmit(e) {
    e.preventDefault()
    runSearch(query)
  }

  return (
    <Layout headerLeft={<div><p className="text-xs text-slate-400">Intelligence</p><p className="text-sm font-medium text-slate-900">AI Semantic Search</p></div>}>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-slate-900 mb-1">AI Semantic Search</h1>
        <p className="text-sm text-slate-500 mb-6">
          Search across every document you have access to, by meaning rather than exact keywords.
        </p>

        <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. what vehicle was involved"
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
        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {results && (
          <div className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
            {results.length === 0 && <p className="p-8 text-sm text-slate-500 text-center">No matches.</p>}
            {results.map((r) => (
              <button
                key={r.chunk_id}
                onClick={() => navigate(`/cases/${encodeURIComponent(r.case_id)}`)}
                className="w-full text-left p-4 hover:bg-slate-50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-500">
                    case {r.case_id} · doc #{r.document_id} · {r.document_type?.replaceAll('_', ' ')}
                  </span>
                  <span className="text-xs text-slate-400">score {r.score.toFixed(3)}</span>
                </div>
                <p className="text-sm text-slate-800">{r.chunk_text}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
