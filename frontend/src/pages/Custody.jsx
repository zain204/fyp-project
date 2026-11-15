import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Link2, ShieldCheck, ShieldAlert, Search } from 'lucide-react'
import { chainApi, evidenceApi, errMsg } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import { useAllEvidence } from '../hooks/useAllEvidence'
import { useToast } from '../context/ToastContext'
import { PageHeader, PageLoader, ErrorState, EmptyState, Hash, Spinner } from '../components/ui/ui'
import CustodyTimeline from '../components/CustodyTimeline'
import { fmtDate } from '../utils/format'

export default function Custody() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  const [sel, setSel] = useState(params.get('e') || '')
  const [q, setQ] = useState('')
  const [vr, setVr] = useState(null)
  const [vBusy, setVBusy] = useState(false)
  const ev = useAllEvidence()
  const chain = useFetch(() => chainApi.chain({ limit: 500 }))
  const cust = useFetch(() => (sel ? evidenceApi.custody(sel) : Promise.resolve(null)), [sel])

  const caseOf = useMemo(() => Object.fromEntries((ev.data?.cases || []).map((c) => [c.id, c.case_number])), [ev.data])
  const blocks = useMemo(() => (chain.data || []).filter((b) => !q || String(b.block_index) === q || String(b.evidence_id) === q || b.block_hash.startsWith(q.toLowerCase()) || (b.evidence_hash || '').startsWith(q.toLowerCase())), [chain.data, q])
  const selEv = ev.data?.evidence.find((e) => String(e.id) === sel)
  const block = chain.data?.find((b) => String(b.evidence_id) === sel)

  const verify = async () => {
    setVBusy(true)
    try { const r = await chainApi.verify(); setVr(r); r.is_valid ? toast.success('Ledger verified') : toast.error(r.message) }
    catch (e) { toast.error(errMsg(e)) } finally { setVBusy(false) }
  }
  const pick = (v) => { setSel(v); v ? setParams({ e: v }) : setParams({}) }

  if (chain.loading || ev.loading) return <PageLoader />
  if (chain.error || ev.error) return <ErrorState message={chain.error || ev.error} onRetry={() => { chain.reload(); ev.reload() }} />

  return (
    <>
      <PageHeader eyebrow="Blockchain custody" title="Custody ledger" subtitle="Evidence files stay in secure storage. The ledger holds only hashes and custody references."
        actions={<button className="btn btn-dark" onClick={verify} disabled={vBusy}>{vBusy ? <Spinner size={15} /> : <ShieldCheck size={16} />} Verify ledger</button>} />

      {vr && (
        <div className={`banner ${vr.is_valid ? 'ok' : 'bad'}`}>
          {vr.is_valid ? <ShieldCheck size={22} /> : <ShieldAlert size={22} />}
          <div><b>{vr.is_valid ? 'Ledger integrity verified' : `Ledger broken${vr.broken_at_index != null ? ` at block #${vr.broken_at_index}` : ''}`}</b>
            <span>{vr.message} · {vr.total_blocks} blocks · checked {fmtDate(vr.checked_at)}</span></div>
        </div>)}

      <section className="card">
        <h3 className="card-title">Chain visualisation</h3>
        {chain.data.length === 0 ? <EmptyState icon={Link2} title="Ledger is empty" text="Blocks are created when evidence is uploaded." /> : (
          <div className="chain-viz">{chain.data.slice(-8).map((b, i, a) => (
            <div className="chain-item" key={b.id}>
              <div className="block"><small>BLOCK</small><b>#{b.block_index}</b><code>{b.block_hash.slice(0, 8)}</code><span>{b.evidence_id ? `EV-${String(b.evidence_id).padStart(4, '0')}` : 'Genesis'}</span></div>
              {i < a.length - 1 && <i className="link-line" />}</div>))}</div>)}
      </section>

      <div className="grid-2-1">
        <section className="card">
          <h3 className="card-title">Ledger blocks ({blocks.length})</h3>
          <div className="input search mb"><Search size={16} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Block #, evidence ID or hash prefix" /></div>
          {blocks.length === 0 ? <EmptyState title="No blocks found" /> : (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Block</th><th>Timestamp</th><th>Evidence</th><th>Case</th><th>Evidence hash</th><th>Previous</th><th>Block hash (tx ref)</th></tr></thead>
              <tbody>{blocks.map((b) => (
                <tr key={b.id} className={String(b.evidence_id) === sel ? 'selected clickable' : 'clickable'} onClick={() => b.evidence_id && pick(String(b.evidence_id))}>
                  <td className="mono">#{b.block_index}</td><td>{fmtDate(b.timestamp)}</td><td className="mono">{b.evidence_id ? `EV-${String(b.evidence_id).padStart(4, '0')}` : 'Genesis'}</td>
                  <td className="mono">{b.case_id ? caseOf[b.case_id] || `#${b.case_id}` : '—'}</td><td><Hash value={b.evidence_hash} /></td><td><Hash value={b.previous_hash} /></td><td><Hash value={b.block_hash} /></td></tr>))}</tbody></table></div>)}
        </section>
        <section className="card">
          <h3 className="card-title">Custody timeline</h3>
          <select className="control mb" value={sel} onChange={(e) => pick(e.target.value)}>
            <option value="">Select evidence…</option>{ev.data.evidence.map((e) => <option key={e.id} value={e.id}>EV-{String(e.id).padStart(4, '0')} · {e.original_filename}</option>)}</select>
          {!sel ? <p className="muted">Pick evidence, or click a ledger row, to see who handled it and when.</p> : (
            <>
              {selEv && <p className="small-note"><b>{selEv.case.case_number}</b> · {block ? `Block #${block.block_index}` : 'No ledger block'}</p>}
              <CustodyTimeline records={cust.data} loading={cust.loading} />
            </>)}
        </section>
      </div>
    </>
  )
}
