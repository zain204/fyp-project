import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { FolderKanban, FolderOpen, FileLock2, Hourglass, AlertOctagon, ShieldCheck, Plus, ArrowRight, Brain } from 'lucide-react'
import { casesApi, evidenceApi } from '../services/api'
import { loadAllEvidence } from '../hooks/useAllEvidence'
import { useFetch } from '../hooks/useFetch'
import { useAuth } from '../context/AuthContext'
import { PageHeader, StatCard, PageLoader, ErrorState, EmptyState, Badge, IntegrationPending } from '../components/ui/ui'
import { FileGlyph } from '../components/EvidenceBits'
import { fmtDate, fmtBytes, label } from '../utils/format'

const SHADES = ['#000000', '#4a4a4a', '#8c8c8c', '#cfcfcf']
export const CUSTODY_LABEL = {
  uploaded: 'Evidence Registered', verified: 'Hash Verified', viewed: 'Evidence Accessed',
  downloaded: 'Evidence Downloaded', analyzed: 'Analysis Performed', transferred: 'Custody Transferred',
}

async function loadDashboard() {
  const [stats, { cases, evidence }] = await Promise.all([casesApi.stats(), loadAllEvidence()])
  // Custody lookups don't write records, so they are safe to use for the activity feed.
  const recent = evidence.slice(0, 6)
  const custody = (await Promise.all(recent.map((e) => evidenceApi.custody(e.id).then((r) => r.map((c) => ({ ...c, evidence: e }))).catch(() => [])))).flat()
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 8)
  return { stats, cases, evidence, custody }
}

export function DashboardView({ admin, extra }) {
  const { user } = useAuth()
  const { data, loading, error, reload } = useFetch(loadDashboard)
  if (loading) return <PageLoader text="Loading dashboard…" />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const { stats, cases, evidence, custody } = data
  const verified = evidence.filter((e) => e.is_verified).length
  const pie = [
    { name: 'Open', value: stats.open }, { name: 'In progress', value: stats.in_progress },
    { name: 'Under review', value: stats.under_review }, { name: 'Closed', value: stats.closed },
  ]
  const byType = Object.entries(cases.reduce((m, c) => ((m[c.crime_type || 'Uncategorised'] = (m[c.crime_type || 'Uncategorised'] || 0) + 1), m), {})).map(([name, value]) => ({ name, value }))
  const recentCases = [...cases].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)).slice(0, 5)

  return (
    <>
      <PageHeader eyebrow={admin ? 'Administrator console' : 'Investigator workspace'} title={`${admin ? 'System overview' : 'Welcome'}, ${user.full_name.split(' ')[0]}`}
        subtitle={admin ? 'Live figures across all cases and evidence.' : 'A live view of your cases, evidence and custody activity.'}
        actions={<Link to="/cases?new=1" className="btn btn-dark"><Plus size={16} /> New case</Link>} />

      <div className="stats">
        <StatCard icon={FolderKanban} label="Total cases" value={stats.total} />
        <StatCard icon={FolderOpen} label="Open cases" value={stats.open} hint={`${stats.in_progress} in progress`} />
        <StatCard icon={FileLock2} label="Evidence items" value={evidence.length} />
        <StatCard icon={Hourglass} label="Pending analysis" pending hint="AI module not connected" />
        <StatCard icon={AlertOctagon} label="High-risk findings" pending hint="AI module not connected" />
        <StatCard icon={ShieldCheck} label="Verified evidence" value={verified} hint={`of ${evidence.length} items`} />
      </div>

      <div className="grid-3">
        <section className="card">
          <h3 className="card-title">Case status distribution</h3>
          {stats.total === 0 ? <EmptyState title="No cases yet" /> : (
            <div className="chart-row">
              <ResponsiveContainer width="55%" height={190}>
                <PieChart><Pie data={pie} dataKey="value" innerRadius={52} outerRadius={80} paddingAngle={2} stroke="#fff">{pie.map((_, i) => <Cell key={i} fill={SHADES[i]} />)}</Pie><Tooltip /></PieChart>
              </ResponsiveContainer>
              <ul className="legend">{pie.map((p, i) => <li key={p.name}><i style={{ background: SHADES[i] }} />{p.name}<b>{p.value}</b></li>)}</ul>
            </div>
          )}
        </section>
        <section className="card">
          <h3 className="card-title">Cases by category</h3>
          {byType.length === 0 ? <EmptyState title="No data" /> : (
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={byType} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid stroke="#eee" horizontal={false} /><XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={92} tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="value" fill="#000" radius={[0, 3, 3, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
        <section className="card">
          <h3 className="card-title">Evidence risk distribution</h3>
          <IntegrationPending title="Awaiting AI analysis module" needs="Risk levels come from AI findings. The analysis routes are not implemented in the backend yet." />
        </section>
      </div>

      <div className="grid-2 gap">
        <section className="card">
          <div className="card-head"><h3 className="card-title">Recent evidence uploads</h3><Link to="/evidence" className="link">View all <ArrowRight size={14} /></Link></div>
          {evidence.length === 0 ? <EmptyState title="No evidence uploaded" text="Upload your first item from Evidence Management." /> : (
            <ul className="list">
              {evidence.slice(0, 5).map((e) => (
                <li key={e.id}><FileGlyph mime={e.file_type} name={e.original_filename} />
                  <div className="grow"><Link to={`/evidence/${e.id}`} className="strong">{e.original_filename}</Link><small>{e.case.case_number} · {fmtBytes(e.file_size)} · {fmtDate(e.uploaded_at)}</small></div>
                  <Badge value={e.is_verified ? 'verified' : 'mismatch'} text={e.is_verified ? 'Verified' : 'Mismatch'} /></li>
              ))}
            </ul>
          )}
        </section>
        <section className="card">
          <div className="card-head"><h3 className="card-title">Recent custody events</h3><Link to="/custody" className="link">Ledger <ArrowRight size={14} /></Link></div>
          {custody.length === 0 ? <EmptyState title="No custody events" /> : (
            <ul className="list">
              {custody.map((c) => (
                <li key={c.id}><span className="dot" />
                  <div className="grow"><span className="strong">{CUSTODY_LABEL[c.action] || label(c.action)}</span><small>{c.evidence.original_filename} · {fmtDate(c.timestamp)}</small></div></li>
              ))}
            </ul>
          )}
        </section>
        <section className="card">
          <div className="card-head"><h3 className="card-title">Recent investigation activity</h3><Link to="/cases" className="link">All cases <ArrowRight size={14} /></Link></div>
          {recentCases.length === 0 ? <EmptyState title="No cases yet" /> : (
            <ul className="list">
              {recentCases.map((c) => (
                <li key={c.id}><div className="grow"><Link to={`/cases/${c.id}`} className="strong">{c.case_number} · {c.title}</Link><small>Updated {fmtDate(c.updated_at)}</small></div><Badge value={c.status} /></li>
              ))}
            </ul>
          )}
        </section>
        <section className="card">
          <h3 className="card-title">Latest AI analysis results</h3>
          <IntegrationPending title="No analysis data available" needs="Results will appear here once analysis endpoints exist in the backend." />
        </section>
      </div>
      {extra}
    </>
  )
}

export default function Dashboard() {
  return <DashboardView />
}
