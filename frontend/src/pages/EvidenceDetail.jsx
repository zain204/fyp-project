import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, ShieldCheck, Trash2, Link2 } from 'lucide-react'
import { evidenceApi, chainApi, errMsg } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, Badge, Hash, ConfirmDialog } from '../components/ui/ui'
import CustodyTimeline from '../components/CustodyTimeline'
import { FileGlyph } from '../components/EvidenceBits'
import { fmtBytes, fmtDate, extOf } from '../utils/format'

export default function EvidenceDetail() {
  const { id } = useParams()
  const { isAdmin } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useFetch(async () => {
    const e = await evidenceApi.get(id) // also logs a "viewed" custody record on the backend
    const [custody, block] = await Promise.all([evidenceApi.custody(id), chainApi.forEvidence(id).catch(() => null)])
    return { e, custody, block }
  }, [id])
  const [del, setDel] = useState(false)
  const [busy, setBusy] = useState(false)

  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const { e, custody, block } = data

  const download = async () => {
    try { await evidenceApi.download(e.id, e.original_filename); toast.success('Download started'); reload() }
    catch (err) { toast.error(err.response?.status ? 'Download failed: file unavailable' : errMsg(err)) }
  }
  const remove = async () => {
    setBusy(true)
    try { await evidenceApi.remove(e.id); toast.success('Evidence deleted'); navigate('/evidence') }
    catch (err) { toast.error(errMsg(err)); setBusy(false) }
  }
  const rows = [
    ['Evidence ID', `EV-${String(e.id).padStart(4, '0')}`], ['Case', <Link key="c" to={`/cases/${e.case_id}`}>Case #{e.case_id}</Link>],
    ['File type (MIME)', e.file_type || '—'], ['Extension', extOf(e.original_filename)], ['File size', `${fmtBytes(e.file_size)} (${e.file_size?.toLocaleString()} bytes)`],
    ['Uploaded', fmtDate(e.uploaded_at)], ['Uploaded by', `User #${e.uploaded_by}`], ['Ledger block', e.blockchain_block_index != null ? `#${e.blockchain_block_index}` : '—'],
  ]
  return (
    <>
      <Link to="/evidence" className="back-link"><ArrowLeft size={15} /> Evidence</Link>
      <PageHeader eyebrow={`EV-${String(e.id).padStart(4, '0')}`} title={e.original_filename} subtitle={e.description || undefined}
        actions={<><Link to={`/integrity?e=${e.id}`} className="btn btn-outline"><ShieldCheck size={15} /> Verify integrity</Link>
          <Link to={`/custody?e=${e.id}`} className="btn btn-outline"><Link2 size={15} /> Custody</Link>
          <button className="btn btn-dark" onClick={download}><Download size={15} /> Download</button>
          {isAdmin && <button className="btn btn-outline danger-text" onClick={() => setDel(true)}><Trash2 size={15} /></button>}</>} />
      <div className="grid-2-1">
        <section className="card">
          <div className="file-hero"><FileGlyph mime={e.file_type} name={e.original_filename} size={34} /><Badge value={e.is_verified ? 'verified' : 'mismatch'} text={e.is_verified ? 'Last check: verified' : 'Last check: mismatch'} /></div>
          <dl className="dl">{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
          <h4 className="sub">SHA-256 (recorded at upload)</h4><Hash value={e.sha256_hash} full />
          {block && <><h4 className="sub">Ledger record</h4><Hash value={block.evidence_hash} full /><small className="muted">Block #{block.block_index} · {block.block_hash.slice(0, 16)}…</small></>}
          <p className="note-box">Extended metadata (EXIF, document properties) is not exposed by the current backend. Only the fields above are available.</p>
        </section>
        <section className="card"><h3 className="card-title">Chain of custody</h3><CustodyTimeline records={custody} /></section>
      </div>
      <ConfirmDialog open={del} danger busy={busy} title="Delete evidence?" confirmText="Delete" onClose={() => setDel(false)} onConfirm={remove} message="The file and database record will be removed. The ledger block remains." />
    </>
  )
}
