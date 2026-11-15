import { useState } from 'react'
import { Brain, Play, ScanText, AlertTriangle, ListChecks, Gauge } from 'lucide-react'
import { useAllEvidence } from '../hooks/useAllEvidence'
import { PageHeader, PageLoader, ErrorState, IntegrationPending, EmptyState } from '../components/ui/ui'

const PANELS = [
  [ScanText, 'OCR-extracted text'], [AlertTriangle, 'Suspicious keywords & threat indicators'],
  [ListChecks, 'AI-generated findings'], [Gauge, 'Preliminary risk score & level'],
]

export default function AIAnalysis() {
  const { data, loading, error, reload } = useAllEvidence()
  const [sel, setSel] = useState('')
  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />
  return (
    <>
      <PageHeader eyebrow="AI forensic analysis" title="AI-assisted evidence analysis" subtitle="Preliminary indicators to support, never replace, the investigator." />
      <div className="banner warn"><AlertTriangle size={20} /><div><b>Preliminary findings only</b><span>AI output requires verification by a human investigator and is not conclusive legal proof.</span></div></div>
      <IntegrationPending title="AI analysis is not available in the backend yet"
        needs="backend/app/api/analysis.py and services/ai_analysis.py are empty, so no analysis, OCR or risk-scoring route exists. The controls below stay disabled and nothing is simulated. Wire them in services/api.js once the routes exist (see services/pending.js)." />
      <section className="card">
        <div className="toolbar tight">
          <select className="control grow" value={sel} onChange={(e) => setSel(e.target.value)}>
            <option value="">Select evidence…</option>{data.evidence.map((e) => <option key={e.id} value={e.id}>EV-{String(e.id).padStart(4, '0')} · {e.original_filename}</option>)}</select>
          <button className="btn btn-dark" disabled title="Backend analysis route not implemented"><Play size={15} /> Start analysis</button>
          <button className="btn btn-outline" disabled>Review findings</button>
          <button className="btn btn-outline" disabled>Confirm findings</button>
          <button className="btn btn-outline" disabled>Download findings</button>
        </div>
      </section>
      <div className="grid-2">
        {PANELS.map(([Icon, t]) => <section className="card" key={t}><h3 className="card-title">{t}</h3><EmptyState icon={Icon} title="No analysis results" text="Results will be displayed here once analysis is available." /></section>)}
      </div>
    </>
  )
}
