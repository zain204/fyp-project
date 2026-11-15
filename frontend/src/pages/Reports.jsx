import { useState } from 'react'
import { FileText, FilePlus2, Download, History } from 'lucide-react'
import { casesApi } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import { PageHeader, PageLoader, ErrorState, IntegrationPending, EmptyState } from '../components/ui/ui'

export default function Reports() {
  const { data, loading, error, reload } = useFetch(() => casesApi.list({ limit: 200 }))
  const [sel, setSel] = useState('')
  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />
  return (
    <>
      <PageHeader eyebrow="Investigation reports" title="Automated reports" subtitle="Case details, evidence metadata, hashes, findings, risk and custody in one PDF." />
      <IntegrationPending title="Report generation is not available in the backend yet"
        needs="backend/app/api/reports.py is empty (the Report database model exists). No PDF is generated or faked. Wire Generate and Download in services/api.js once the routes exist (see services/pending.js)." />
      <section className="card">
        <div className="toolbar tight">
          <select className="control grow" value={sel} onChange={(e) => setSel(e.target.value)}>
            <option value="">Select a case…</option>{data.map((c) => <option key={c.id} value={c.id}>{c.case_number} — {c.title}</option>)}</select>
          <button className="btn btn-dark" disabled title="Backend report route not implemented"><FilePlus2 size={15} /> Generate report</button>
          <button className="btn btn-outline" disabled><Download size={15} /> Download PDF</button>
        </div>
      </section>
      <div className="grid-2">
        <section className="card"><h3 className="card-title">Report history</h3><EmptyState icon={History} title="No reports" text="Generated reports will be listed here." /></section>
        <section className="card"><h3 className="card-title">Report details</h3><EmptyState icon={FileText} title="No report selected" /></section>
      </div>
    </>
  )
}
