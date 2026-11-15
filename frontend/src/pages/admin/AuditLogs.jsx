import { ScrollText } from 'lucide-react'
import { PageHeader, IntegrationPending, EmptyState } from '../../components/ui/ui'

// Verified in backend/app/api/*.py — these are written to the audit_logs table today.
const RECORDED = ['SIGNUP', 'LOGIN', 'LOGIN_FAILED', 'CREATE_CASE', 'UPDATE_CASE', 'DELETE_CASE', 'UPLOAD_EVIDENCE', 'DOWNLOAD_EVIDENCE', 'VERIFY_EVIDENCE', 'DELETE_EVIDENCE']

export default function AuditLogs() {
  return (
    <>
      <PageHeader eyebrow="Security" title="Audit logs" subtitle="Accountability trail of user and system activity." />
      <IntegrationPending title="No route to read audit logs yet" needs="The backend already writes audit rows (user, action, resource, details, IP, timestamp) but exposes no endpoint to read them. Add a GET route restricted to admins, then build the table here. Logout is not recorded because the backend has no logout route.">
        <div className="chips">{RECORDED.map((r) => <span key={r} className="chip-d mono">{r}</span>)}</div>
      </IntegrationPending>
      <section className="card"><EmptyState icon={ScrollText} title="No log data available" /></section>
    </>
  )
}
