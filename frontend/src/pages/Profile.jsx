import { useEffect } from 'react'
import { LogOut } from 'lucide-react'
import { authApi } from '../services/api'
import { tokenStore } from '../services/tokenStore'
import { useAuth } from '../context/AuthContext'
import { PageHeader, Badge } from '../components/ui/ui'
import { fmtDate } from '../utils/format'

export default function Profile() {
  const { user, signOut } = useAuth()
  useEffect(() => { authApi.me().then(tokenStore.setUser.bind(tokenStore)).catch(() => {}) }, [])
  const initials = user.full_name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
  const exp = tokenStore.expiry()
  return (
    <>
      <PageHeader eyebrow="Account" title="Profile" />
      <section className="card profile">
        <div className="avatar xl">{initials}</div>
        <div className="grow">
          <h2>{user.full_name}</h2>
          <div className="badges"><Badge value={user.role} /><Badge value={user.is_active ? 'active' : 'inactive'} /></div>
          <dl className="dl">{[['Email', user.email], ['User ID', `#${user.id}`], ['Badge number', user.badge_number || '—'], ['Member since', fmtDate(user.created_at, false)], ['Session expires', exp ? fmtDate(new Date(exp).toISOString()) : '—']].map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
          <button className="btn btn-outline" onClick={() => signOut()}><LogOut size={15} /> Logout</button>
        </div>
      </section>
    </>
  )
}
