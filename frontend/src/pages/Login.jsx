import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mfaPendingToken, setMfaPendingToken] = useState(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const { setToken } = useAuth()
  const navigate = useNavigate()

  async function handlePasswordSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await api.login(email, password)
      if (result.mfa_required) {
        setMfaPendingToken(result.mfa_pending_token)
      } else {
        await setToken(result.access_token)
        navigate('/')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleMfaSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await api.verifyMfa(mfaPendingToken, code)
      await setToken(result.access_token)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900 mb-1">Secure document system</h1>
        <p className="text-sm text-slate-500 mb-6">Legal &amp; investigation document access</p>

        {!mfaPendingToken ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-800 disabled:opacity-50"
            >
              {busy ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleMfaSubmit} className="space-y-4">
            <p className="text-sm text-slate-600">Enter the 6-digit code from your authenticator app.</p>
            <input
              type="text"
              required
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-slate-400"
              placeholder="000000"
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-800 disabled:opacity-50"
            >
              {busy ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        )}

        <p className="text-sm text-slate-500 mt-6 text-center">
          No account? <Link to="/register" className="text-slate-900 underline">Register</Link>
        </p>
      </div>
    </div>
  )
}
