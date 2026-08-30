const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000'

function authHeaders() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function handle(resp) {
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      // response wasn't JSON - keep statusText
    }
    throw new Error(detail)
  }
  if (resp.status === 204) return null
  return resp.json()
}

export const api = {
  register: (payload) =>
    fetch(`${GATEWAY_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handle),

  login: (email, password) =>
    fetch(`${GATEWAY_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(handle),

  verifyMfa: (mfa_pending_token, code) =>
    fetch(`${GATEWAY_URL}/api/auth/login/verify-mfa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mfa_pending_token, code }),
    }).then(handle),

  me: () => fetch(`${GATEWAY_URL}/api/auth/me`, { headers: authHeaders() }).then(handle),

  mfaSetup: () =>
    fetch(`${GATEWAY_URL}/api/auth/mfa/setup`, { method: 'POST', headers: authHeaders() }).then(handle),

  mfaConfirm: (code) =>
    fetch(`${GATEWAY_URL}/api/auth/mfa/confirm`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    }).then(handle),

  listDocuments: (caseId) =>
    fetch(`${GATEWAY_URL}/api/documents${caseId ? `?case_id=${encodeURIComponent(caseId)}` : ''}`, {
      headers: authHeaders(),
    }).then(handle),

  uploadDocument: (caseId, documentType, file) => {
    const form = new FormData()
    form.append('case_id', caseId)
    form.append('document_type', documentType)
    form.append('file', file)
    return fetch(`${GATEWAY_URL}/api/documents/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    }).then(handle)
  },

  downloadDocument: async (docId) => {
    const resp = await fetch(`${GATEWAY_URL}/api/documents/${docId}/download`, { headers: authHeaders() })
    if (!resp.ok) throw new Error(await resp.text())
    return resp.blob()
  },

  verifyDocumentIntegrity: (docId) =>
    fetch(`${GATEWAY_URL}/api/documents/${docId}/verify-integrity`, { headers: authHeaders() }).then(handle),

  indexForSearch: (documentId, caseId, documentType, text) =>
    fetch(`${GATEWAY_URL}/api/search/index`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: String(documentId), case_id: caseId, document_type: documentType, text }),
    }).then(handle),

  search: (query, caseId) =>
    fetch(
      `${GATEWAY_URL}/api/search?q=${encodeURIComponent(query)}${caseId ? `&case_id=${encodeURIComponent(caseId)}` : ''}`,
      { headers: authHeaders() },
    ).then(handle),

  auditLog: (caseId) =>
    fetch(`${GATEWAY_URL}/api/audit/log${caseId ? `?case_id=${encodeURIComponent(caseId)}` : ''}`, {
      headers: authHeaders(),
    }).then(handle),

  auditVerify: () => fetch(`${GATEWAY_URL}/api/audit/verify`, { headers: authHeaders() }).then(handle),

  createCase: (caseNumber, title, description, priority) =>
    fetch(`${GATEWAY_URL}/api/cases`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_number: caseNumber, title, description, priority }),
    }).then(handle),

  listCases: (statusFilter) =>
    fetch(`${GATEWAY_URL}/api/cases${statusFilter ? `?status_filter=${statusFilter}` : ''}`, {
      headers: authHeaders(),
    }).then(handle),

  getCase: (caseNumber) =>
    fetch(`${GATEWAY_URL}/api/cases/${encodeURIComponent(caseNumber)}`, { headers: authHeaders() }).then(handle),

  updateCaseStatus: (caseNumber, status) =>
    fetch(`${GATEWAY_URL}/api/cases/${encodeURIComponent(caseNumber)}/status`, {
      method: 'PATCH',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }).then(handle),

  caseStats: () => fetch(`${GATEWAY_URL}/api/cases/stats`, { headers: authHeaders() }).then(handle),
}
