import { Link } from 'react-router-dom'
import { ShieldHalf } from 'lucide-react'
import { BRAND } from '../../config'
import { scrollToId } from './PublicLayout'

export default function Footer() {
  return (
    <footer className="pfooter">
      <div className="container footer-grid">
        <div>
          <div className="logo"><ShieldHalf size={22} /><span>{BRAND}</span></div>
          <p>AI-Powered Crime Investigation & Forensic Evidence Management. Built as a Final Year Project at COMSATS University Islamabad.</p>
        </div>
        <div>
          <h4>Platform</h4>
          {[['About', 'about'], ['Services', 'services'], ['How It Works', 'how'], ['Modules', 'modules']].map(([t, id]) => (
            <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); scrollToId(id) }}>{t}</a>
          ))}
        </div>
        <div>
          <h4>Access</h4>
          <Link to="/login">Investigator Login</Link>
          <Link to="/admin/login">Administrator Login</Link>
          <Link to="/signup">Create Account</Link>
        </div>
        <div>
          <h4>Notice</h4>
          <p>AI-generated findings are preliminary and must be verified by a human investigator. They are not conclusive legal proof.</p>
        </div>
      </div>
      <div className="container footer-bottom"><span>© {new Date().getFullYear()} {BRAND}. Academic project.</span><span>Design inspired by institutional forensic portals; not affiliated with any agency.</span></div>
    </footer>
  )
}
