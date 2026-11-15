import { Link, useLocation } from 'react-router-dom'
import { useAuth, homeFor } from '../context/AuthContext'

export function NotFound() {
  const { user } = useAuth()
  return <div className="fullpage"><h1>404</h1><p>This page does not exist.</p><Link className="btn btn-dark" to={user ? homeFor(user) : '/'}>Go back</Link></div>
}
export function Unauthorized() {
  const { user } = useAuth()
  const { state } = useLocation()
  return <div className="fullpage"><h1>Access denied</h1><p>Your role does not have permission to open this page.</p><Link className="btn btn-dark" to={state?.home || homeFor(user)}>Return to my workspace</Link></div>
}
