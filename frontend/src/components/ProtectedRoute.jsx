import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth, homeFor } from '../context/AuthContext'
import { PageLoader } from './ui/ui'

// <ProtectedRoute roles={['admin']} /> — renders child routes only for allowed roles.
export default function ProtectedRoute({ roles }) {
  const { user, booting } = useAuth()
  const location = useLocation()
  if (booting) return <div style={{ height: '100vh' }}><PageLoader text="Restoring session…" /></div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  if (roles && !roles.includes(user.role)) return <Navigate to="/unauthorized" replace state={{ home: homeFor(user) }} />
  return <Outlet />
}
