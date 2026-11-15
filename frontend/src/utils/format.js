// Backend datetimes are naive UTC (no "Z"), so mark them as UTC before parsing.
export function toDate(v) {
  if (!v) return null
  const s = String(v)
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : `${s}Z`)
}
export function fmtDate(v, withTime = true) {
  const d = toDate(v)
  if (!d || isNaN(d)) return '—'
  return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  })
}
export function fmtBytes(n) {
  if (n == null) return '—'
  if (n < 1024) return `${n} B`
  const u = ['KB', 'MB', 'GB']
  let i = -1
  do { n /= 1024; i++ } while (n >= 1024 && i < u.length - 1)
  return `${n.toFixed(n < 10 ? 2 : 1)} ${u[i]}`
}
export const label = (s) => (s ? s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : '—')
export const shortHash = (h, n = 10) => (h ? `${h.slice(0, n)}…${h.slice(-6)}` : '—')
export const extOf = (name) => (name && name.includes('.') ? name.split('.').pop().toLowerCase() : '—')
