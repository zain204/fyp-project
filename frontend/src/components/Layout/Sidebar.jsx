import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, FolderKanban, FileLock2, Brain, ShieldCheck, Link2, FileText,
  UserCircle, LogOut, Users, ScrollText, ShieldHalf, X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { BRAND } from '../../config'

const INVESTIGATOR = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/cases', label: 'Cases', icon: FolderKanban },
  { to: '/evidence', label: 'Evidence Management', icon: FileLock2 },
  { to: '/analysis', label: 'AI Analysis', icon: Brain },
  { to: '/integrity', label: 'Integrity Verification', icon: ShieldCheck },
  { to: '/custody', label: 'Blockchain Custody', icon: Link2 },
  { to: '/reports', label: 'Investigation Reports', icon: FileText },
  { to: '/profile', label: 'Profile', icon: UserCircle },
]
const ADMIN = [
  { to: '/admin', label: 'Admin Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/users', label: 'User Management', icon: Users },
  { to: '/cases', label: 'All Cases', icon: FolderKanban },
  { to: '/evidence', label: 'Evidence', icon: FileLock2 },
  { to: '/integrity', label: 'Integrity Verification', icon: ShieldCheck },
  { to: '/custody', label: 'Blockchain Ledger', icon: Link2 },
  { to: '/admin/audit', label: 'Audit Logs', icon: ScrollText },
  { to: '/profile', label: 'Profile', icon: UserCircle },
]

export default function Sidebar({ open, onClose }) {
  const { isAdmin, signOut } = useAuth()
  const items = isAdmin ? ADMIN : INVESTIGATOR
  return (
    <>
      <div className={`scrim ${open ? 'show' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sb-brand">
          <ShieldHalf size={22} /><span>{BRAND}</span>
          <button className="icon-btn sb-close" onClick={onClose} aria-label="Close menu"><X size={18} /></button>
        </div>
        <div className="sb-role">{isAdmin ? 'Administrator Console' : 'Investigator Workspace'}</div>
        <nav>
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to + label} to={to} end={end} onClick={onClose} className={({ isActive }) => `sb-link ${isActive ? 'active' : ''}`}>
              <Icon size={18} strokeWidth={1.6} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <button className="sb-link sb-logout" onClick={() => signOut()}>
          <LogOut size={18} strokeWidth={1.6} /><span>Logout</span>
        </button>
      </aside>
    </>
  )
}
