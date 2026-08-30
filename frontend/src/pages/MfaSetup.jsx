import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

export default function MfaSetup() {
  const { user, refreshUser } = useAuth()
  const [setup, setSetup] = useState(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)
  const navigate = useNavigate()

  async function handleStart() {
    setError(null)
    try {
      setSetup(await api.mfaSetup())
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleConfirm(e) {
    e.preventDefault()
    setError(null)
    try {
      await api.mfaConfirm(code)
      await refreshUser()
      setDone(true)
      setTimeout(() => navigate('/'), 1200)
    } catch (err) {
      setError(err.message)
    }
  }

  if (user?.mfa_enabled && !setup) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-full max-w-sm bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
          <p className="text-sm text-slate-700">MFA is already enabled on this account.</p>
          <Link to="/" className="text-sm text-slate-900 underline mt-4 inline-block">Back to dashboard</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900 mb-6">Enable MFA</h1>

        {done ? (
          <p className="text-sm text-green-700">MFA enabled. Redirecting...</p>
        ) : !setup ? (
          <>
            <p className="text-sm text-slate-600 mb-4">
              Adds a required 6-digit code from an authenticator app (Google Authenticator, Authy) at login.
            </p>
            <button
              onClick={handleStart}
              className="w-full rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-800"
            >
              Start setup
            </button>
          </>
        ) : (
          <form onSubmit={handleConfirm} className="space-y-4">
            <div>
              <p className="text-sm text-slate-600 mb-2">
                Scan this in your authenticator app, or enter the secret manually:
              </p>
              <code className="block text-xs bg-slate-100 rounded p-2 break-all">{setup.provisioning_uri}</code>
              <p className="text-xs text-slate-500 mt-2">Secret: <code>{setup.secret}</code></p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Enter the code it generates to confirm
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-slate-400"
                placeholder="000000"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              className="w-full rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-800"
            >
              Confirm and enable
            </button>
          </form>
        )}

        <p className="text-sm text-slate-500 mt-6 text-center">
          <Link to="/" className="text-slate-900 underline">Back to dashboard</Link>
        </p>
      </div>
    </div>
  )
}
