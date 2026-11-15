import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X, ShieldHalf, ArrowUpRight } from 'lucide-react'
import { useAuth, homeFor } from '../../context/AuthContext'
import { BRAND } from '../../config'

const LINKS = [
  ['Home', 'home'], ['About Us', 'about'], ['Services', 'services'],
  ['How It Works', 'how'], ['Modules', 'modules'], ['Contact', 'contact'],
]

export function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function PublicLayout() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [solid, setSolid] = useState(false)
  const navigate = useNavigate()
  const { pathname, state } = useLocation()

  useEffect(() => {
    const h = () => setSolid(window.scrollY > 30)
    h(); window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  // Landing links from other public pages come back with a target section.
  useEffect(() => { if (pathname === '/' && state?.scrollTo) setTimeout(() => scrollToId(state.scrollTo), 80) }, [pathname, state])

  const go = (id) => {
    setOpen(false)
    if (pathname === '/') scrollToId(id)
    else navigate('/', { state: { scrollTo: id } })
  }

  return (
    <div className="public">
      <header className={`pnav ${solid || pathname !== '/' ? 'solid' : ''}`}>
        <div className="container pnav-in">
          <Link to="/" className="logo"><ShieldHalf size={24} /><span>{BRAND}</span></Link>
          <nav className={`plinks ${open ? 'open' : ''}`}>
            {LINKS.map(([t, id]) => <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); go(id) }}>{t}</a>)}
            <div className="plinks-cta">
              {user ? (
                <Link to={homeFor(user)} className="btn btn-light sm">Open Workspace <ArrowUpRight size={15} /></Link>
              ) : (
                <>
                  <NavLink to="/login" className="btn btn-ghost sm" onClick={() => setOpen(false)}>Login</NavLink>
                  <NavLink to="/signup" className="btn btn-light sm" onClick={() => setOpen(false)}>Sign Up</NavLink>
                </>
              )}
            </div>
          </nav>
          <button className="icon-btn pnav-toggle" onClick={() => setOpen((o) => !o)} aria-label="Menu">{open ? <X /> : <Menu />}</button>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
