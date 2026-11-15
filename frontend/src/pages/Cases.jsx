import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, Search, LayoutGrid, Rows3, Pencil, Trash2, FolderKanban, ChevronLeft, ChevronRight } from 'lucide-react'
import { casesApi, errMsg } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, EmptyState, Badge, ConfirmDialog } from '../components/ui/ui'
import CaseFormModal from '../components/CaseFormModal'
import { CASE_STATUSES, CASE_PRIORITIES } from '../config'
import { fmtDate, label } from '../utils/format'

const LIMIT = 12

export default function Cases() {
  const { user, isAdmin } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [search, setSearch] = useState(params.get('search') || '')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [page, setPage] = useState(0)
  const [view, setView] = useState('table')
  const [form, setForm] = useState({ open: params.get('new') === '1', existing: null })
  const [del, setDel] = useState(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState(search)

  // Debounce the text box; keep the URL (?search=) in sync so the top-bar search works.
  useEffect(() => { const t = setTimeout(() => { setQ(search); setPage(0) }, 300); return () => clearTimeout(t) }, [search])
  useEffect(() => { const s = params.get('search') || ''; setSearch(s) }, [params])
  useEffect(() => { if (params.get('new') === '1') { params.delete('new'); setParams(params, { replace: true }) } }, []) // eslint-disable-line

  const { data, loading, error, reload } = useFetch(
    () => casesApi.list({ search: q || undefined, status: status || undefined, priority: priority || undefined, skip: page * LIMIT, limit: LIMIT }),
    [q, status, priority, page],
  )

  const remove = async () => {
    setBusy(true)
    try { await casesApi.remove(del.id); toast.success(`${del.case_number} deleted`); setDel(null); reload() }
    catch (e) { toast.error(errMsg(e)) } finally { setBusy(false) }
  }
  const who = (c) => (c.investigator_id === user.id ? 'You' : `Investigator #${c.investigator_id}`)
  const filtered = !!(q || status || priority)

  return (
    <>
      <PageHeader eyebrow="Case management" title={isAdmin ? 'All cases' : 'My cases'} subtitle="Create, search and track cybercrime investigations."
        actions={<button className="btn btn-dark" onClick={() => setForm({ open: true, existing: null })}><Plus size={16} /> New case</button>} />

      <div className="toolbar">
        <div className="input search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by title or case number" /></div>
        <select className="control" value={status} onChange={(e) => { setStatus(e.target.value); setPage(0) }}>
          <option value="">All statuses</option>{CASE_STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select>
        <select className="control" value={priority} onChange={(e) => { setPriority(e.target.value); setPage(0) }}>
          <option value="">All priorities</option>{CASE_PRIORITIES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select>
        <div className="seg">
          <button className={view === 'table' ? 'on' : ''} onClick={() => setView('table')} aria-label="Table view"><Rows3 size={16} /></button>
          <button className={view === 'cards' ? 'on' : ''} onClick={() => setView('cards')} aria-label="Card view"><LayoutGrid size={16} /></button>
        </div>
        {filtered && <button className="btn btn-ghost-dark sm" onClick={() => { setSearch(''); setStatus(''); setPriority(''); params.delete('search'); setParams(params) }}>Clear filters</button>}
      </div>

      {loading ? <PageLoader /> : error ? <ErrorState message={error} onRetry={reload} /> : data.length === 0 ? (
        <div className="card"><EmptyState icon={FolderKanban} title={filtered ? 'No cases match your filters' : 'No cases yet'} text={filtered ? 'Try a different search or clear the filters.' : 'Create your first case to start collecting evidence.'}
          action={!filtered && <button className="btn btn-dark" onClick={() => setForm({ open: true, existing: null })}><Plus size={16} /> Create case</button>} /></div>
      ) : view === 'table' ? (
        <div className="card table-card"><div className="table-wrap"><table className="table">
          <thead><tr><th>Case ID</th><th>Title</th><th>Category</th><th>Priority</th><th>Status</th><th>Investigator</th><th>Created</th><th /></tr></thead>
          <tbody>{data.map((c) => (
            <tr key={c.id} className="clickable" onClick={() => navigate(`/cases/${c.id}`)}>
              <td className="mono">{c.case_number}</td><td className="strong">{c.title}</td><td>{c.crime_type || '—'}</td>
              <td><Badge value={c.priority} /></td><td><Badge value={c.status} /></td><td>{who(c)}</td><td>{fmtDate(c.created_at, false)}</td>
              <td className="row-actions" onClick={(e) => e.stopPropagation()}>
                <button className="icon-btn" title="Update" onClick={() => setForm({ open: true, existing: c })}><Pencil size={15} /></button>
                {isAdmin && <button className="icon-btn" title="Delete" onClick={() => setDel(c)}><Trash2 size={15} /></button>}
              </td></tr>))}</tbody></table></div></div>
      ) : (
        <div className="case-grid">{data.map((c) => (
          <div key={c.id} className="case-card">
            <div className="case-card-top"><span className="mono">{c.case_number}</span><Badge value={c.priority} /></div>
            <Link to={`/cases/${c.id}`}><h3>{c.title}</h3></Link>
            <p className="muted clamp">{c.description || 'No description provided.'}</p>
            <div className="case-card-meta"><span>{c.crime_type || 'Uncategorised'}</span><Badge value={c.status} /></div>
            <div className="case-card-foot"><small>{who(c)} · {fmtDate(c.created_at, false)}</small>
              <span><button className="icon-btn" title="Update" onClick={() => setForm({ open: true, existing: c })}><Pencil size={15} /></button>
                {isAdmin && <button className="icon-btn" title="Delete" onClick={() => setDel(c)}><Trash2 size={15} /></button>}</span></div>
          </div>))}</div>
      )}

      {!loading && !error && (page > 0 || data.length === LIMIT) && (
        <div className="pager"><button className="btn btn-outline sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={15} /> Previous</button>
          <span>Page {page + 1}</span><button className="btn btn-outline sm" disabled={data.length < LIMIT} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight size={15} /></button></div>
      )}

      <CaseFormModal open={form.open} existing={form.existing} onClose={() => setForm({ open: false, existing: null })} onSaved={reload} />
      <ConfirmDialog open={!!del} danger busy={busy} title="Delete case?" confirmText="Delete case" onClose={() => setDel(null)} onConfirm={remove}
        message={`This permanently deletes ${del?.case_number} together with its evidence records, notes and reports. Ledger blocks remain in the chain.`} />
    </>
  )
}
