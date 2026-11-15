import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Upload, Search, Download, Trash2, ShieldCheck, FileLock2 } from 'lucide-react'
import { useAllEvidence } from '../hooks/useAllEvidence'
import { evidenceApi, errMsg } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, EmptyState, Badge, Modal, ConfirmDialog, Hash } from '../components/ui/ui'
import UploadPanel from '../components/UploadPanel'
import { FileGlyph } from '../components/EvidenceBits'
import { fmtBytes, fmtDate, extOf } from '../utils/format'

export default function Evidence() {
  const { user, isAdmin } = useAuth()
  const toast = useToast()
  const { data, loading, error, reload } = useAllEvidence()
  const [q, setQ] = useState('')
  const [caseF, setCaseF] = useState('')
  const [stat, setStat] = useState('')
  const [up, setUp] = useState(false)
  const [del, setDel] = useState(null)
  const [busy, setBusy] = useState(false)
  const [dl, setDl] = useState(null)

  const rows = useMemo(() => (data?.evidence || []).filter((e) =>
    (!q || e.original_filename.toLowerCase().includes(q.toLowerCase()) || e.sha256_hash.startsWith(q.toLowerCase()) || String(e.id) === q) &&
    (!caseF || String(e.case_id) === caseF) && (!stat || (stat === 'verified') === e.is_verified)), [data, q, caseF, stat])

  const download = async (e) => {
    setDl(e.id)
    try { await evidenceApi.download(e.id, e.original_filename); toast.success('Download started. Recorded in custody log.') }
    catch (err) { toast.error(err.response?.status ? 'Download failed: file unavailable' : errMsg(err)) } finally { setDl(null) }
  }
  const remove = async () => {
    setBusy(true)
    try { await evidenceApi.remove(del.id); toast.success('Evidence deleted'); setDel(null); reload() }
    catch (e) { toast.error(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <>
      <PageHeader eyebrow="Evidence management" title="Digital evidence" subtitle="Every file is hashed with SHA-256 and recorded on the ledger at upload."
        actions={<button className="btn btn-dark" onClick={() => setUp(true)}><Upload size={16} /> Upload evidence</button>} />
      {loading ? <PageLoader /> : error ? <ErrorState message={error} onRetry={reload} /> : (
        <>
          <div className="toolbar">
            <div className="input search"><Search size={16} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search file name, ID or hash prefix" /></div>
            <select className="control" value={caseF} onChange={(e) => setCaseF(e.target.value)}><option value="">All cases</option>{data.cases.map((c) => <option key={c.id} value={c.id}>{c.case_number}</option>)}</select>
            <select className="control" value={stat} onChange={(e) => setStat(e.target.value)}><option value="">All statuses</option><option value="verified">Verified</option><option value="mismatch">Mismatch</option></select>
          </div>
          {rows.length === 0 ? <div className="card"><EmptyState icon={FileLock2} title={data.evidence.length ? 'No evidence matches your filters' : 'No evidence uploaded'} text={data.evidence.length ? undefined : 'Upload files and attach them to a case.'} action={!data.evidence.length && <button className="btn btn-dark" onClick={() => setUp(true)}><Upload size={16} /> Upload evidence</button>} /></div> : (
            <div className="card table-card"><div className="table-wrap"><table className="table">
              <thead><tr><th>ID</th><th>File</th><th>Type</th><th>Size</th><th>Case</th><th>SHA-256</th><th>Uploaded</th><th>By</th><th>Status</th><th /></tr></thead>
              <tbody>{rows.map((e) => (
                <tr key={e.id}>
                  <td className="mono">EV-{String(e.id).padStart(4, '0')}</td>
                  <td><div className="cell-file"><FileGlyph mime={e.file_type} name={e.original_filename} /><Link className="strong" to={`/evidence/${e.id}`}>{e.original_filename}</Link></div></td>
                  <td title={e.file_type}>{extOf(e.original_filename).toUpperCase()}</td><td>{fmtBytes(e.file_size)}</td>
                  <td><Link to={`/cases/${e.case_id}`} className="mono">{e.case.case_number}</Link></td><td><Hash value={e.sha256_hash} /></td>
                  <td>{fmtDate(e.uploaded_at)}</td><td>{e.uploaded_by === user.id ? 'You' : `User #${e.uploaded_by}`}</td>
                  <td><Badge value={e.is_verified ? 'verified' : 'mismatch'} text={e.is_verified ? 'Verified' : 'Mismatch'} /></td>
                  <td className="row-actions">
                    <Link className="icon-btn" title="Verify integrity" to={`/integrity?e=${e.id}`}><ShieldCheck size={15} /></Link>
                    <button className="icon-btn" title="Download" onClick={() => download(e)} disabled={dl === e.id}><Download size={15} /></button>
                    {isAdmin && <button className="icon-btn" title="Delete" onClick={() => setDel(e)}><Trash2 size={15} /></button>}
                  </td></tr>))}</tbody></table></div></div>)}
        </>)}
      <Modal open={up} wide title="Upload digital evidence" onClose={() => setUp(false)}>
        <UploadPanel cases={data?.cases || []} onUploaded={reload} onClose={() => setUp(false)} /></Modal>
      <ConfirmDialog open={!!del} danger busy={busy} title="Delete evidence?" confirmText="Delete evidence" onClose={() => setDel(null)} onConfirm={remove}
        message={`Delete "${del?.original_filename}"? The file and database record are removed. Its ledger block stays in the chain.`} />
    </>
  )
}
