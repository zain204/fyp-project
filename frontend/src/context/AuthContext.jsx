import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { tokenStore } from '../services/tokenStore'
import * as authService from '../services/auth'
import { useToast } from './ToastContext'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)
export const homeFor = (user) => (user?.role === 'admin' ? '/admin' : '/dashboard')

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (tokenStore.get() ? tokenStore.user() : null))
  const [booting, setBooting] = useState(!!tokenStore.get())
  const navigate = useNavigate()
  const toast = useToast()

  const signOut = useCallback(
    (message) => {
      authService.logout()
      setUser(null)
      if (message) toast.info(message)
      navigate('/login', { replace: true })
    },
    [navigate, toast],
  )

  // Validate the stored token against /auth/me on first load.
  useEffect(() => {
    if (!tokenStore.get()) { setBooting(false); return }
    authApi.me()
      .then((u) => { setUser(u); tokenStore.setUser(u) })
      .catch(() => { authService.logout(); setUser(null) })
      .finally(() => setBooting(false))
  }, [])

  // 401 from any request, or JWT expiry → end the session.
  useEffect(() => {
    const onExpired = () => signOut('Your session has expired. Please sign in again.')
    window.addEventListener('auth:expired', onExpired)
    const exp = tokenStore.expiry()
    let timer
    if (user && exp) timer = setTimeout(onExpired, Math.max(exp - Date.now(), 0))
    return () => { window.removeEventListener('auth:expired', onExpired); clearTimeout(timer) }
  }, [user, signOut])

  const login = async (creds) => {
    const u = await authService.login(creds)
    setUser(u)
    return u
  }

  return (
    <AuthCtx.Provider value={{ user, booting, login, signOut, isAdmin: user?.role === 'admin' }}>
      {children}
    </AuthCtx.Provider>
  )
}
