// Top bar of the authenticated app: menu button, global case search, user menu.
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Search, ChevronDown, LogOut, UserCircle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function Navbar({ onMenu }) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [menu, setMenu] = useState(false)
  const box = useRef(null)

  useEffect(() => {
    const h = (e) => box.current && !box.current.contains(e.target) && setMenu(false)
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  const submit = (e) => {
    e.preventDefault()
    navigate(q.trim() ? `/cases?search=${encodeURIComponent(q.trim())}` : '/cases')
  }
  const initials = (user?.full_name || '?').split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <header className="topbar">
      <button className="icon-btn menu-btn" onClick={onMenu} aria-label="Open menu"><Menu size={20} /></button>
      <form className="searchbar" onSubmit={submit}>
        <Search size={16} />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search cases by title or case number…" />
      </form>
      <div className="user-menu" ref={box}>
        <button className="user-btn" onClick={() => setMenu((m) => !m)}>
          <span className="avatar">{initials}</span>
          <span className="user-meta"><b>{user?.full_name}</b><small>{user?.role}</small></span>
          <ChevronDown size={14} />
        </button>
        {menu && (
          <div className="dropdown">
            <button onClick={() => { setMenu(false); navigate('/profile') }}><UserCircle size={15} /> My profile</button>
            <button onClick={() => signOut()}><LogOut size={15} /> Logout</button>
          </div>
        )}
      </div>
    </header>
  )
}
