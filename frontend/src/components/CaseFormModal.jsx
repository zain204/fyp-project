import { useEffect, useState } from 'react'
import { Modal, Field, Spinner } from './ui/ui'
import { casesApi, errMsg } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { CRIME_TYPES, CASE_STATUSES, CASE_PRIORITIES } from '../config'
import { label } from '../utils/format'

const blank = { title: '', description: '', crime_type: CRIME_TYPES[0], priority: 'medium', status: 'open', investigator_id: '' }

export default function CaseFormModal({ open, onClose, existing, onSaved }) {
  const { isAdmin } = useAuth()
  const toast = useToast()
  const [f, setF] = useState(blank)
  const [errors, setErrors] = useState({})
  const [apiErr, setApiErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    setErrors({}); setApiErr('')
    setF(existing ? {
      title: existing.title, description: existing.description || '', crime_type: existing.crime_type || '',
      priority: existing.priority, status: existing.status, investigator_id: '',
    } : blank)
  }, [open, existing])

  const types = f.crime_type && !CRIME_TYPES.includes(f.crime_type) ? [...CRIME_TYPES, f.crime_type] : CRIME_TYPES
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const save = async () => {
    const er = {}
    if (f.title.trim().length < 3) er.title = 'Title must be at least 3 characters'
    if (f.title.length > 200) er.title = 'Title must be 200 characters or fewer'
    if (f.investigator_id !== '' && !/^\d+$/.test(String(f.investigator_id))) er.investigator_id = 'Enter a numeric user ID'
    setErrors(er); setApiErr('')
    if (Object.keys(er).length) return
    setBusy(true)
    try {
      const body = { title: f.title.trim(), description: f.description.trim() || null, crime_type: f.crime_type || null, priority: f.priority }
      if (existing) body.status = f.status
      if (isAdmin && f.investigator_id !== '') body.investigator_id = Number(f.investigator_id)
      const saved = existing ? await casesApi.update(existing.id, body) : await casesApi.create(body)
      toast.success(existing ? 'Case updated' : `Case ${saved.case_number} created`)
      onSaved?.(saved)
      onClose()
    } catch (e) { setApiErr(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <Modal open={open} onClose={onClose} wide title={existing ? `Update ${existing.case_number}` : 'Create new case'}
      footer={<><button className="btn btn-outline" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="btn btn-dark" onClick={save} disabled={busy}>{busy && <Spinner size={14} />}{existing ? 'Save changes' : 'Create case'}</button></>}>
      <div className="form">
        {apiErr && <div className="alert alert-error">{apiErr}</div>}
        <Field label="Case title" error={errors.title}><input className="control" value={f.title} onChange={set('title')} placeholder="e.g. Phishing campaign targeting bank customers" /></Field>
        <div className="grid-2">
          <Field label="Crime category"><select className="control" value={f.crime_type} onChange={set('crime_type')}>{types.map((t) => <option key={t}>{t}</option>)}</select></Field>
          <Field label="Priority"><select className="control" value={f.priority} onChange={set('priority')}>{CASE_PRIORITIES.map((p) => <option key={p} value={p}>{label(p)}</option>)}</select></Field>
        </div>
        {existing && <Field label="Investigation status"><select className="control" value={f.status} onChange={set('status')}>{CASE_STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select></Field>}
        <Field label="Description"><textarea className="control" rows="4" value={f.description} onChange={set('description')} placeholder="Summary of the incident and investigation scope" /></Field>
        {isAdmin && <Field label={existing ? 'Reassign to investigator (user ID)' : 'Assign to investigator (user ID)'} error={errors.investigator_id} hint="Admin only. Leave empty to keep the default. The backend has no user-list route yet, so enter the numeric ID.">
          <input className="control" inputMode="numeric" value={f.investigator_id} onChange={set('investigator_id')} placeholder="e.g. 2" /></Field>}
      </div>
    </Modal>
  )
}
