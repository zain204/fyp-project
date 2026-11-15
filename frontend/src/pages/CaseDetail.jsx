import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Pencil, Trash2, Upload, FileLock2 } from 'lucide-react'
import { casesApi, evidenceApi, errMsg } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, EmptyState, Badge, ConfirmDialog, Modal } from '../components/ui/ui'
import CaseFormModal from '../components/CaseFormModal'
import UploadPanel from '../components/UploadPanel'
import { FileGlyph } from '../components/EvidenceBits'
import { fmtDate, fmtBytes } from '../utils/format'

export default function CaseDetail() {
  const { id } = useParams()
  const { user, isAdmin } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useFetch(() => Promise.all([casesApi.get(id), evidenceApi.byCase(id)]), [id])
  const [edit, setEdit] = useState(false)
  const [del, setDel] = useState(false)
  const [up, setUp] = useState(false)
  const [busy, setBusy] = useState(false)

  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const [c, evidence] = data

  const remove = async () => {
    setBusy(true)
    try { await casesApi.remove(c.id); toast.success(`${c.case_number} deleted`); navigate('/cases') }
    catch (e) { toast.error(errMsg(e)); setBusy(false) }
  }
  const rows = [
    ['Case ID', c.case_number], ['Category', c.crime_type || '—'], ['Created', fmtDate(c.created_at)], ['Last updated', fmtDate(c.updated_at)],
    ['Assigned investigator', c.investigator_id === user.id ? `You (#${c.investigator_id})` : `Investigator #${c.investigator_id}`],
  ]
  return (
    <>
      <Link to="/cases" className="back-link"><ArrowLeft size={15} /> All cases</Link>
      <PageHeader eyebrow={c.case_number} title={c.title}
        actions={<><button className="btn btn-outline" onClick={() => setEdit(true)}><Pencil size={15} /> Update</button>
          {isAdmin && <button className="btn btn-outline danger-text" onClick={() => setDel(true)}><Trash2 size={15} /> Delete</button>}
          <button className="btn btn-dark" onClick={() => setUp(true)}><Upload size={15} /> Upload evidence</button></>} />
      <div className="grid-2-1">
        <section className="card">
          <h3 className="card-title">Case information</h3>
          <div className="badges"><Badge value={c.status} /><Badge value={c.priority} text={`${c.priority} priority`} /></div>
          <p className="desc">{c.description || <span className="muted">No description provided.</span>}</p>
          <dl className="dl">{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
        </section>
        <section className="card">
          <h3 className="card-title">Associated evidence ({evidence.length})</h3>
          {evidence.length === 0 ? <EmptyState icon={FileLock2} title="No evidence yet" text="Upload the first item for this case." /> : (
            <ul className="list">{evidence.map((e) => (
              <li key={e.id}><FileGlyph mime={e.file_type} name={e.original_filename} />
                <div className="grow"><Link className="strong" to={`/evidence/${e.id}`}>{e.original_filename}</Link><small>{fmtBytes(e.file_size)} · {fmtDate(e.uploaded_at)}</small></div>
                <Badge value={e.is_verified ? 'verified' : 'mismatch'} text={e.is_verified ? 'Verified' : 'Mismatch'} /></li>))}</ul>)}
        </section>
      </div>
      <CaseFormModal open={edit} existing={c} onClose={() => setEdit(false)} onSaved={reload} />
      <Modal open={up} wide title="Upload evidence" onClose={() => setUp(false)}><UploadPanel cases={[c]} defaultCaseId={c.id} onUploaded={reload} onClose={() => setUp(false)} /></Modal>
      <ConfirmDialog open={del} danger busy={busy} title="Delete case?" confirmText="Delete case" onClose={() => setDel(false)} onConfirm={remove} message={`Permanently delete ${c.case_number} and all of its evidence records?`} />
    </>
  )
}
