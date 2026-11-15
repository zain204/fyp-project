import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ShieldCheck, ShieldAlert, ShieldX, ShieldQuestion, CheckCircle2, XCircle, MinusCircle } from 'lucide-react'
import { useAllEvidence } from '../hooks/useAllEvidence'
import { evidenceApi, errMsg } from '../services/api'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, EmptyState, Hash, Spinner } from '../components/ui/ui'
import { fmtBytes, fmtDate, extOf } from '../utils/format'

// Maps backend VerifyResult.status to the four indicators the UI shows.
const STATES = {
  pending: { icon: ShieldQuestion, title: 'Pending', text: 'Not verified in this session. Run a verification.', cls: 'pending' },
  intact: { icon: ShieldCheck, title: 'Verified', text: 'Hash matches the database and the ledger.', cls: 'ok' },
  tampered: { icon: ShieldAlert, title: 'Integrity Mismatch', text: 'The recalculated hash does not match the recorded hash.', cls: 'bad' },
  missing: { icon: ShieldX, title: 'Verification Failed', text: 'The evidence file is missing from storage.', cls: 'bad' },
  ledger_broken: { icon: ShieldAlert, title: 'Ledger Broken', text: 'File is original but the blockchain chain failed validation.', cls: 'bad' },
  error: { icon: ShieldX, title: 'Verification Failed', text: 'The verification request could not be completed.', cls: 'bad' },
}

function Compare({ label, value, ok }) {
  const Icon = ok === true ? CheckCircle2 : ok === false ? XCircle : MinusCircle
  return (
    <div className={`cmp ${ok === true ? 'ok' : ok === false ? 'bad' : ''}`}>
      <div className="cmp-h"><Icon size={16} />{label}</div>
      {value ? <Hash value={value} full /> : <span className="muted">Not available</span>}
    </div>
  )
}

export default function Integrity() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const { data, loading, error, reload } = useAllEvidence()
  const [sel, setSel] = useState(params.get('e') || '')
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [fail, setFail] = useState('')

  useEffect(() => { setRes(null); setFail('') }, [sel])
  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const ev = data.evidence.find((e) => String(e.id) === sel)

  const pick = (v) => { setSel(v); v ? setParams({ e: v }) : setParams({}) }
  const run = async () => {
    setBusy(true); setFail('')
    try {
      const r = await evidenceApi.verify(ev.id)
      setRes(r)
      r.is_intact ? toast.success('Evidence verified: integrity intact') : toast.error(r.message)
      reload()
    } catch (e) { setFail(errMsg(e)); toast.error('Verification failed') } finally { setBusy(false) }
  }
  const key = fail ? 'error' : res ? res.status : 'pending'
  const S = STATES[key] || STATES.error
  const dbMatch = res?.current_hash ? res.current_hash.toLowerCase() === res.original_hash.toLowerCase() : res ? false : null
  const ledMatch = res?.blockchain_verified ?? null

  return (
    <>
      <PageHeader eyebrow="Integrity verification" title="SHA-256 evidence verification" subtitle="Recalculates the file hash and compares it with the database record and the blockchain ledger." />
      <section className="card">
        <label className="field"><span className="field-label">Evidence item</span>
          <select className="control" value={sel} onChange={(e) => pick(e.target.value)}>
            <option value="">Select evidence…</option>
            {data.evidence.map((e) => <option key={e.id} value={e.id}>EV-{String(e.id).padStart(4, '0')} · {e.original_filename} ({e.case.case_number})</option>)}
          </select></label>
      </section>

      {!ev ? <div className="card"><EmptyState icon={ShieldCheck} title={data.evidence.length ? 'Select an evidence item' : 'No evidence available'} text={data.evidence.length ? 'Choose a file above to inspect and verify it.' : 'Upload evidence first.'} /></div> : (
        <div className="grid-2-1">
          <section className="card">
            <h3 className="card-title">Evidence record</h3>
            <dl className="dl">
              {[['Evidence ID', `EV-${String(ev.id).padStart(4, '0')}`], ['File name', ev.original_filename], ['File extension', extOf(ev.original_filename)], ['MIME type', ev.file_type || '—'],
                ['File size', fmtBytes(ev.file_size)], ['Uploaded (timestamp)', fmtDate(ev.uploaded_at)], ['Last verified at', res ? fmtDate(res.verified_at) : '—']].map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}
            </dl>
            <h4 className="sub">SHA-256 hash (recorded)</h4><Hash value={ev.sha256_hash} full />
          </section>
          <section className="card verify-card">
            <div className={`verdict ${S.cls}`}><S.icon size={46} strokeWidth={1.2} /><h3>{S.title}</h3><p>{fail || res?.message || S.text}</p></div>
            <button className="btn btn-dark lg block" onClick={run} disabled={busy}>{busy ? <Spinner size={16} /> : <ShieldCheck size={17} />} Verify integrity</button>
            <small className="muted center">Last recorded status: {ev.is_verified ? 'verified' : 'mismatch'}</small>
          </section>
          {res && (
            <section className="card span-all">
              <h3 className="card-title">Hash comparison</h3>
              <div className="cmp-grid">
                <Compare label="Original recorded hash (database)" value={res.original_hash} />
                <Compare label="Recalculated hash (current file)" value={res.current_hash} ok={dbMatch} />
                <Compare label={`Ledger hash${res.block_index != null ? ` (block #${res.block_index})` : ''}`} value={res.blockchain_hash} ok={ledMatch} />
              </div>
              <div className="chips">
                <span className="chip-d">Database match: {dbMatch === null ? 'n/a' : dbMatch ? 'yes' : 'no'}</span>
                <span className="chip-d">Ledger match: {ledMatch === null ? 'no block' : ledMatch ? 'yes' : 'no'}</span>
                <span className="chip-d">Chain valid: {res.chain_valid == null ? 'n/a' : res.chain_valid ? 'yes' : 'no'}</span>
              </div>
            </section>
          )}
        </div>
      )}
    </>
  )
}
