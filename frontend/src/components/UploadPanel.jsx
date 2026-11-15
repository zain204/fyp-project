import { useRef, useState } from 'react'
import { UploadCloud, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { evidenceApi, errMsg } from '../services/api'
import { useToast } from '../context/ToastContext'
import { Field } from './ui/ui'
import { FileGlyph } from './EvidenceBits'
import { MAX_UPLOAD_MB } from '../config'
import { fmtBytes } from '../utils/format'

// Uploads one file at a time to POST /evidence/upload (case_id, description, file).
export default function UploadPanel({ cases, defaultCaseId, onUploaded, onClose }) {
  const toast = useToast()
  const input = useRef(null)
  const [caseId, setCaseId] = useState(defaultCaseId ? String(defaultCaseId) : '')
  const [description, setDescription] = useState('')
  const [items, setItems] = useState([]) // {id, file, state: queued|uploading|done|error, progress, error}
  const [drag, setDrag] = useState(false)
  const [running, setRunning] = useState(false)
  const [caseErr, setCaseErr] = useState('')

  const add = (files) => {
    const next = Array.from(files).map((file) => {
      let error = null
      if (file.size === 0) error = 'File is empty'
      else if (file.size > MAX_UPLOAD_MB * 1024 * 1024) error = `Larger than ${MAX_UPLOAD_MB} MB limit`
      return { id: `${file.name}-${file.size}-${Math.random()}`, file, state: error ? 'error' : 'queued', progress: 0, error, invalid: !!error }
    })
    setItems((p) => [...p, ...next])
  }
  const patch = (id, v) => setItems((p) => p.map((i) => (i.id === id ? { ...i, ...v } : i)))

  const start = async () => {
    if (!caseId) { setCaseErr('Select the case this evidence belongs to'); return }
    setCaseErr('')
    const queue = items.filter((i) => !i.invalid && (i.state === 'queued' || i.state === 'error'))
    if (!queue.length) { toast.error('Add at least one valid file'); return }
    setRunning(true)
    let ok = 0
    for (const it of queue) {
      patch(it.id, { state: 'uploading', progress: 0, error: null })
      try {
        const fd = new FormData()
        fd.append('case_id', caseId)
        if (description.trim()) fd.append('description', description.trim())
        fd.append('file', it.file)
        await evidenceApi.upload(fd, (p) => patch(it.id, { progress: p }))
        patch(it.id, { state: 'done', progress: 100 }); ok++
      } catch (e) { patch(it.id, { state: 'error', error: errMsg(e) }) }
    }
    setRunning(false)
    if (ok) { toast.success(`${ok} evidence file${ok > 1 ? 's' : ''} uploaded, hashed and recorded on the ledger`); onUploaded?.() }
    if (ok < queue.length) toast.error('Some files failed. See details below.')
  }

  const pending = items.filter((i) => !i.invalid && i.state !== 'done').length

  return (
    <div className="form">
      <Field label="Case" error={caseErr}>
        <select className="control" value={caseId} onChange={(e) => setCaseId(e.target.value)} disabled={running}>
          <option value="">Select a case…</option>
          {cases.map((c) => <option key={c.id} value={c.id}>{c.case_number} — {c.title}</option>)}
        </select>
      </Field>
      <Field label="Description (optional)"><input className="control" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Screenshot of phishing e-mail" disabled={running} /></Field>

      <div className={`dropzone ${drag ? 'drag' : ''}`} onClick={() => input.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files) }}>
        <UploadCloud size={36} strokeWidth={1.2} />
        <b>Drag &amp; drop files here</b><span>or click to browse · max {MAX_UPLOAD_MB} MB per file</span>
        <input ref={input} type="file" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      </div>

      {items.length > 0 && (
        <ul className="upload-list">
          {items.map((i) => (
            <li key={i.id} className={`up-${i.state}`}>
              <FileGlyph mime={i.file.type} name={i.file.name} />
              <div className="grow"><span className="strong">{i.file.name}</span><small>{fmtBytes(i.file.size)}{i.error && <em> · {i.error}</em>}</small>
                {i.state === 'uploading' && <div className="progress"><i style={{ width: `${i.progress}%` }} /></div>}</div>
              {i.state === 'done' && <CheckCircle2 size={18} />}
              {i.state === 'error' && <AlertCircle size={18} />}
              {i.state === 'uploading' && <Loader2 size={18} className="spin" />}
              {!running && i.state !== 'done' && <button className="icon-btn sm" onClick={() => setItems((p) => p.filter((x) => x.id !== i.id))} aria-label="Remove"><X size={14} /></button>}
            </li>))}
        </ul>
      )}
      <div className="modal-foot-inline">
        {onClose && <button className="btn btn-outline" onClick={onClose} disabled={running}>Close</button>}
        <button className="btn btn-dark" onClick={start} disabled={running || items.length === 0}>{running ? 'Uploading…' : `Upload${pending ? ` ${pending} file${pending > 1 ? 's' : ''}` : ''}`}</button>
      </div>
    </div>
  )
}
