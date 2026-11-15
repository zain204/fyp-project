import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight, ShieldCheck, Brain, Link2, FileText, FolderKanban, FileLock2, Fingerprint, ScanText,
  Hash as HashIcon, Users, ScrollText, Mail, MapPin, Lock, Layers, Eye, CheckCircle2,
} from 'lucide-react'
import Footer from '../../components/Layout/Footer'
import { scrollToId } from '../../components/Layout/PublicLayout'
import { CONTACT_EMAIL } from '../../config'

function HeroVisual() {
  const rows = ['9f86d081884c7d65', '9a2feaa0c55ad015', 'a3c721fbdd8a2f9b', '6b3a55e0261b0304']
  return (
    <div className="hero-visual" aria-hidden="true">
      <svg viewBox="0 0 520 520" className="hv-rings">
        {[230, 180, 130, 80].map((r, i) => (
          <circle key={r} cx="260" cy="260" r={r} fill="none" stroke="currentColor" strokeOpacity={0.12 + i * 0.05} strokeDasharray={i % 2 ? '2 8' : '0'} className={`ring ring-${i}`} />
        ))}
        <circle cx="260" cy="260" r="230" fill="none" stroke="currentColor" strokeOpacity=".5" strokeDasharray="60 1385" className="sweep" />
      </svg>
      <div className="hv-core"><Fingerprint size={92} strokeWidth={0.9} /></div>
      <div className="hv-card hv-a"><small>SHA-256</small>{rows.slice(0, 2).map((r) => <code key={r}>{r}</code>)}<span className="hv-ok"><CheckCircle2 size={13} /> Integrity verified</span></div>
      <div className="hv-card hv-b"><small>Ledger</small><div className="hv-chain">{[0, 1, 2, 3].map((i) => <i key={i} />)}</div><code>block #0042 · linked</code></div>
      <div className="hv-card hv-c"><small>AI triage</small><div className="hv-bar"><i style={{ width: '68%' }} /></div><code>Preliminary · needs review</code></div>
    </div>
  )
}

const SERVICES = [
  { icon: FolderKanban, t: 'Case Management', d: 'Open cybercrime cases, assign investigators, track status and priority from first report to closure.' },
  { icon: FileLock2, t: 'Secure Evidence Storage', d: 'Evidence files are stored in controlled file storage with every upload recorded against its case.' },
  { icon: HashIcon, t: 'SHA-256 Integrity', d: 'A cryptographic hash is computed at upload and can be recomputed at any time to detect tampering.' },
  { icon: Brain, t: 'AI-Assisted Analysis', d: 'OCR, keyword detection and risk indicators give investigators a preliminary lead, always subject to human review.' },
  { icon: Link2, t: 'Blockchain Custody', d: 'Evidence hashes are chained in a tamper-evident ledger so any alteration of the record is detectable.' },
  { icon: FileText, t: 'Investigation Reports', d: 'Case, evidence, hash, finding and custody information compiled into a formal report.' },
]
const STEPS = [
  ['Register the case', 'Create a case with its category, priority and description.'],
  ['Upload evidence', 'Files are stored, hashed with SHA-256 and written to the ledger.'],
  ['Verify integrity', 'Recompute the hash and compare it with the database and the ledger.'],
  ['Analyse', 'AI and OCR highlight suspicious content for investigator review.'],
  ['Preserve custody', 'Every access and action is recorded in the chain of custody.'],
  ['Report', 'Produce a structured report for the case file.'],
]
const MODULES = [
  [Users, 'Authentication & Roles', 'JWT sessions with Administrator and Investigator roles.'],
  [FolderKanban, 'Case Management', 'Create, search, filter and update investigations.'],
  [FileLock2, 'Evidence Management', 'Drag-and-drop upload with SHA-256 at ingestion.'],
  [ShieldCheck, 'Integrity Verification', 'Database and ledger hash comparison on demand.'],
  [ScanText, 'OCR & AI Analysis', 'Text extraction, indicators and preliminary risk scoring.'],
  [Link2, 'Custody Ledger', 'Hash-linked blocks with full-chain verification.'],
  [FileText, 'Reports', 'Automated investigation reports as PDF.'],
  [ScrollText, 'Audit Logs', 'Accountability trail of system activity.'],
]
const WHY = [
  [Lock, 'Tamper-evident by design', 'Hashes in both the database and the ledger make silent modification detectable.'],
  [Eye, 'Human-in-the-loop AI', 'Findings are labelled preliminary. Investigators confirm or reject them.'],
  [Layers, 'One unified workflow', 'From intake to report, every step lives in a single platform.'],
  [Users, 'Role-based access', 'Investigators see their cases; administrators oversee the system.'],
]

export default function Landing() {
  const [active, setActive] = useState(0)
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const [err, setErr] = useState({})
  const S = SERVICES[active]

  const send = (e) => {
    e.preventDefault()
    const er = {}
    if (form.name.trim().length < 2) er.name = 'Enter your name'
    if (!/^\S+@\S+\.\S+$/.test(form.email)) er.email = 'Enter a valid e-mail'
    if (form.message.trim().length < 10) er.message = 'Write at least 10 characters'
    setErr(er)
    if (Object.keys(er).length) return
    const body = `${form.message}\n\n— ${form.name} (${form.email})`
    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Platform enquiry from ' + form.name)}&body=${encodeURIComponent(body)}`
  }

  return (
    <>
      <section id="home" className="hero">
        <div className="hero-grid" />
        <div className="container hero-in">
          <div className="hero-copy">
            <div className="chip"><span className="pulse" /> Digital Forensics Laboratory Platform</div>
            <h1>AI-Powered Crime Investigation &amp; Forensic Evidence Management</h1>
            <h2>Intelligent Digital Forensics. Secure Evidence Management. Trusted Investigation.</h2>
            <p>A centralized platform designed to manage, preserve, and analyze digital evidence using artificial intelligence, forensic technologies, and secure evidence integrity mechanisms.</p>
            <div className="hero-cta">
              <button className="btn btn-light lg" onClick={() => scrollToId('about')}>Explore Platform <ArrowRight size={18} /></button>
              <Link to="/login" className="btn btn-outline-light lg">Investigator Login</Link>
              <button className="btn btn-link-light" onClick={() => scrollToId('services')}>Discover Our Services</button>
            </div>
            <div className="hero-stats">
              <div><b>SHA-256</b><span>Evidence hashing</span></div>
              <div><b>Ledger</b><span>Hash-chained custody</span></div>
              <div><b>2 Roles</b><span>Admin &amp; Investigator</span></div>
            </div>
          </div>
          <HeroVisual />
        </div>
      </section>

      <section id="about" className="section">
        <div className="container split">
          <div>
            <div className="eyebrow">About our platform</div>
            <h2 className="display">Evidence you can defend, from upload to report.</h2>
          </div>
          <div className="about-text">
            <p>Digital evidence is fragile. A single altered byte can undermine an investigation. This platform protects the integrity of every item from the moment it is uploaded, records who touched it, and helps investigators find what matters faster.</p>
            <p>Evidence files stay in secure file storage. Only their hashes and custody details are written to the blockchain-style ledger, so the record stays tamper-evident without exposing sensitive content.</p>
            <div className="about-points">
              {['Cybercrime case tracking', 'Hash-verified evidence', 'Preliminary AI triage', 'Complete audit trail'].map((p) => <span key={p}><CheckCircle2 size={16} /> {p}</span>)}
            </div>
          </div>
        </div>
      </section>

      <section id="services" className="section dark">
        <div className="container">
          <div className="eyebrow">Our core services</div>
          <h2 className="display">Everything an investigation needs.</h2>
          <div className="services">
            <div className="service-list">
              {SERVICES.map((s, i) => (
                <button key={s.t} className={`service ${i === active ? 'on' : ''}`} onMouseEnter={() => setActive(i)} onClick={() => setActive(i)}>
                  <s.icon size={22} strokeWidth={1.5} /><span>{s.t}</span><ArrowRight size={16} />
                </button>
              ))}
            </div>
            <div className="service-detail" key={active}>
              <S.icon size={44} strokeWidth={1} />
              <h3>{S.t}</h3>
              <p>{S.d}</p>
              <Link to="/login" className="btn btn-light">Access the platform <ArrowRight size={16} /></Link>
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="section">
        <div className="container">
          <div className="eyebrow">How the system works</div>
          <h2 className="display">An investigation workflow in six steps.</h2>
          <ol className="steps">
            {STEPS.map(([t, d], i) => (
              <li key={t}><span className="step-n">{String(i + 1).padStart(2, '0')}</span><h4>{t}</h4><p>{d}</p></li>
            ))}
          </ol>
        </div>
      </section>

      <section id="modules" className="section alt">
        <div className="container">
          <div className="eyebrow">Modules &amp; key features</div>
          <h2 className="display">Eight modules, one platform.</h2>
          <div className="module-grid">
            {MODULES.map(([Icon, t, d]) => (
              <div className="module" key={t}><Icon size={24} strokeWidth={1.4} /><h4>{t}</h4><p>{d}</p></div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="eyebrow">Why choose our platform</div>
          <h2 className="display">Built around trust.</h2>
          <div className="why-grid">
            {WHY.map(([Icon, t, d]) => <div key={t} className="why"><Icon size={26} strokeWidth={1.3} /><div><h4>{t}</h4><p>{d}</p></div></div>)}
          </div>
          <div className="notice"><Brain size={20} /><p><b>Responsible AI.</b> AI-generated findings are preliminary indicators only. They require verification by a human investigator and are not conclusive legal proof.</p></div>
        </div>
      </section>

      <section id="contact" className="section dark">
        <div className="container contact">
          <div>
            <div className="eyebrow">Contact</div>
            <h2 className="display">Questions about the platform?</h2>
            <p className="muted-light">Send a message and your mail application will open with it ready to send.</p>
            <div className="contact-lines"><span><Mail size={16} /> {CONTACT_EMAIL}</span><span><MapPin size={16} /> COMSATS University Islamabad, Pakistan</span></div>
          </div>
          <form className="contact-form" onSubmit={send} noValidate>
            <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />{err.name && <em>{err.name}</em>}</label>
            <label>E-mail<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />{err.email && <em>{err.email}</em>}</label>
            <label>Message<textarea rows="4" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />{err.message && <em>{err.message}</em>}</label>
            <button className="btn btn-light lg">Send message <ArrowRight size={16} /></button>
          </form>
        </div>
      </section>
      <Footer />
    </>
  )
}
