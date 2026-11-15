import axios from 'axios'
import { API_URL } from '../config'
import { tokenStore } from './tokenStore'

export const client = axios.create({ baseURL: API_URL, timeout: 60000 })

client.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const isAuthCall = err.config?.url?.includes('/auth/login') || err.config?.url?.includes('/auth/signup')
    if (err.response?.status === 401 && !isAuthCall && tokenStore.get()) {
      tokenStore.clear()
      window.dispatchEvent(new Event('auth:expired'))
    }
    return Promise.reject(err)
  },
)

// Turns any FastAPI / network error into a readable message.
export function errMsg(err, fallback = 'Something went wrong') {
  if (!err) return fallback
  if (err.code === 'ERR_NETWORK') return 'Cannot reach the backend. Is the API server running?'
  const d = err.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => `${(x.loc || []).slice(1).join('.')}: ${x.msg}`).join(' · ')
  return err.message || fallback
}

// ---------- Auth ----------
export const authApi = {
  signup: (body) => client.post('/auth/signup', body).then((r) => r.data),
  login: (body) => client.post('/auth/login', body).then((r) => r.data),
  me: () => client.get('/auth/me').then((r) => r.data),
}

// ---------- Cases ----------
export const casesApi = {
  list: (params) => client.get('/cases/', { params }).then((r) => r.data),
  stats: () => client.get('/cases/stats/summary').then((r) => r.data),
  get: (id) => client.get(`/cases/${id}`).then((r) => r.data),
  create: (body) => client.post('/cases/', body).then((r) => r.data),
  update: (id, body) => client.put(`/cases/${id}`, body).then((r) => r.data),
  remove: (id) => client.delete(`/cases/${id}`),
}

// ---------- Evidence ----------
// GET /evidence/{id} writes a "viewed" custody record on the backend, so concurrent
// identical calls (React StrictMode double effects) are collapsed into one request.
const inflight = new Map()
export const evidenceApi = {
  upload: (formData, onProgress) =>
    client
      .post('/evidence/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 0,
        onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded * 100) / e.total)),
      })
      .then((r) => r.data),
  byCase: (caseId) => client.get(`/evidence/case/${caseId}`).then((r) => r.data),
  get: (id) => {
    if (!inflight.has(id)) {
      const p = client.get(`/evidence/${id}`).then((r) => r.data).finally(() => setTimeout(() => inflight.delete(id), 800))
      inflight.set(id, p)
    }
    return inflight.get(id)
  },
  custody: (id) => client.get(`/evidence/${id}/custody`).then((r) => r.data),
  verify: (id) => client.post(`/evidence/${id}/verify`).then((r) => r.data),
  remove: (id) => client.delete(`/evidence/${id}`),
  async download(id, filename) {
    const res = await client.get(`/evidence/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  },
}

// ---------- Blockchain ledger ----------
export const chainApi = {
  chain: (params) => client.get('/blockchain/chain', { params }).then((r) => r.data),
  verify: () => client.get('/blockchain/verify').then((r) => r.data),
  forEvidence: (evidenceId) => client.get(`/blockchain/evidence/${evidenceId}`).then((r) => r.data),
}
