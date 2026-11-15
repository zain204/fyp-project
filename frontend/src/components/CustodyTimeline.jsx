import { useAuth } from '../context/AuthContext'
import { fmtDate, label } from '../utils/format'
import { Spinner } from './ui/ui'

const LABEL = { uploaded: 'Evidence Registered', verified: 'Hash Verified', viewed: 'Evidence Accessed', downloaded: 'Evidence Downloaded', analyzed: 'Analysis Performed', transferred: 'Custody Transferred' }

export default function CustodyTimeline({ records, loading }) {
  const { user } = useAuth()
  if (loading) return <div className="page-loader sm"><Spinner /> Loading custody records…</div>
  if (!records?.length) return <p className="muted">No custody records.</p>
  return (
    <ol className="timeline">
      {records.map((r) => (
        <li key={r.id}>
          <i />
          <div><b>{LABEL[r.action] || label(r.action)}</b>
            <small>{fmtDate(r.timestamp)} · {r.user_id === user.id ? 'You' : `User #${r.user_id}`}{r.ip_address ? ` · ${r.ip_address}` : ''}</small>
            {r.notes && <code className="note">{r.notes}</code>}</div>
        </li>))}
    </ol>
  )
}
