import { CheckCircle2, CircleDashed } from 'lucide-react'
import { DashboardView } from '../Dashboard'
import { BACKEND } from '../../services/pending'

const MODULES = [
  ['auth', 'Authentication & roles'], ['cases', 'Case management'], ['evidence', 'Evidence upload & storage'], ['integrity', 'SHA-256 verification'],
  ['ledger', 'Blockchain ledger'], ['analysis', 'AI analysis & OCR'], ['reports', 'PDF reports'], ['users', 'User management API'], ['auditLogs', 'Audit log API'],
]

export default function AdminDashboard() {
  return (
    <DashboardView admin extra={
      <section className="card mt">
        <h3 className="card-title">Backend module status</h3>
        <div className="mod-status">{MODULES.map(([k, t]) => (
          <div key={k} className={BACKEND[k] ? 'on' : 'off'}>{BACKEND[k] ? <CheckCircle2 size={16} /> : <CircleDashed size={16} />}<span>{t}</span><em>{BACKEND[k] ? 'Connected' : 'Pending'}</em></div>))}</div>
      </section>} />
  )
}
