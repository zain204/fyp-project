import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, ShieldHalf, Lock, Mail, User, BadgeCheck, KeyRound, ArrowLeft } from 'lucide-react'
import { useAuth, homeFor } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { signup } from '../services/auth'
import { errMsg } from '../services/api'
import { Spinner } from './ui/ui'
import { BRAND } from '../config'

function AuthFrame({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth-side">
        <Link to="/" className="logo"><ShieldHalf size={24} /><span>{BRAND}</span></Link>
        <div>
          <h2>Evidence integrity.<br />Investigator trust.</h2>
          <p>Every upload hashed. Every action recorded. Every finding reviewed by a human.</p>
        </div>
        <small>Final Year Project · COMSATS University Islamabad</small>
      </aside>
      <main className="auth-main">
        <Link to="/" className="back-link"><ArrowLeft size={15} /> Back to website</Link>
        <div className="auth-card">
          <h1>{title}</h1>
          <p className="muted">{subtitle}</p>
          {children}
          <div className="auth-foot">{footer}</div>
        </div>
      </main>
    </div>
  )
}

function Input({ icon: Icon, error, right, ...p }) {
  return (
    <div className="input-wrap">
      <div className={`input ${error ? 'has-error' : ''}`}>
        <Icon size={16} />
        <input {...p} />
        {right}
      </div>
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}

const EMAIL_RE = /^\S+@\S+\.\S+$/

export function LoginForm({ role }) {
  const { user, login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [f, setF] = useState({ email: '', password: '', remember: true })
  const [show, setShow] = useState(false)
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [apiErr, setApiErr] = useState('')
  const isAdmin = role === 'admin'

  if (user) return <Navigate to={homeFor(user)} replace />

  const submit = async (e) => {
    e.preventDefault()
    const er = {}
    if (!EMAIL_RE.test(f.email)) er.email = 'Enter a valid e-mail address'
    if (!f.password) er.password = 'Password is required'
    setErrors(er); setApiErr('')
    if (Object.keys(er).length) return
    setBusy(true)
    try {
      const u = await login({ email: f.email.trim(), password: f.password, role, remember: f.remember })
      toast.success(`Welcome back, ${u.full_name.split(' ')[0]}`)
      const from = location.state?.from
      const allowed = from && (u.role === 'admin' || !from.startsWith('/admin'))
      navigate(allowed ? from : homeFor(u), { replace: true })
    } catch (err) {
      setApiErr(errMsg(err, 'Login failed'))
    } finally { setBusy(false) }
  }

  return (
    <AuthFrame
      title={isAdmin ? 'Administrator login' : 'Investigator login'}
      subtitle={isAdmin ? 'Restricted console for system administrators.' : 'Sign in to your investigation workspace.'}
      footer={<>
        <span>{isAdmin ? 'Are you an investigator?' : 'Are you an administrator?'} <Link to={isAdmin ? '/login' : '/admin/login'}>{isAdmin ? 'Investigator login' : 'Administrator login'}</Link></span>
        <span>No account? <Link to={isAdmin ? '/admin/signup' : '/signup'}>Sign up</Link></span>
      </>}>
      <form onSubmit={submit} noValidate className="form">
        {apiErr && <div className="alert alert-error" role="alert">{apiErr}</div>}
        <label className="field"><span className="field-label">Email</span>
          <Input icon={Mail} type="email" autoComplete="email" placeholder="you@agency.gov.pk" value={f.email} error={errors.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
        </label>
        <label className="field"><span className="field-label">Password</span>
          <Input icon={Lock} type={show ? 'text' : 'password'} autoComplete="current-password" placeholder="Your password" value={f.password} error={errors.password}
            onChange={(e) => setF({ ...f, password: e.target.value })}
            right={<button type="button" className="icon-btn sm" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'}>{show ? <EyeOff size={16} /> : <Eye size={16} />}</button>} />
        </label>
        <label className="check"><input type="checkbox" checked={f.remember} onChange={(e) => setF({ ...f, remember: e.target.checked })} /> Remember me on this device</label>
        <button className="btn btn-dark lg block" disabled={busy}>{busy && <Spinner size={16} />} Sign in</button>
      </form>
    </AuthFrame>
  )
}

export function SignupForm({ role }) {
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const isAdmin = role === 'admin'
  const [f, setF] = useState({ full_name: '', email: '', password: '', confirm: '', badge_number: '', admin_code: '' })
  const [show, setShow] = useState(false)
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [apiErr, setApiErr] = useState('')

  if (user) return <Navigate to={homeFor(user)} replace />
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const er = {}
    // Rules mirror backend UserCreate: name 2–100, valid e-mail, password 8–72, badge ≤ 50.
    if (f.full_name.trim().length < 2 || f.full_name.length > 100) er.full_name = 'Full name must be 2–100 characters'
    if (!EMAIL_RE.test(f.email)) er.email = 'Enter a valid e-mail address'
    if (f.password.length < 8) er.password = 'Password must be at least 8 characters'
    else if (f.password.length > 72) er.password = 'Password must be 72 characters or fewer'
    if (f.confirm !== f.password) er.confirm = 'Passwords do not match'
    if (f.badge_number.length > 50) er.badge_number = 'Badge number is too long'
    if (isAdmin && !f.admin_code.trim()) er.admin_code = 'Administrator code is required'
    setErrors(er); setApiErr('')
    if (Object.keys(er).length) return
    setBusy(true)
    try {
      await signup({
        full_name: f.full_name.trim(), email: f.email.trim(), password: f.password,
        role: isAdmin ? 'admin' : 'investigator',
        badge_number: f.badge_number.trim() || null,
        admin_code: isAdmin ? f.admin_code : null,
      })
      toast.success('Account created. You can sign in now.')
      navigate(isAdmin ? '/admin/login' : '/login', { replace: true })
    } catch (err) {
      setApiErr(errMsg(err, 'Registration failed'))
    } finally { setBusy(false) }
  }

  return (
    <AuthFrame
      title={isAdmin ? 'Create administrator account' : 'Create investigator account'}
      subtitle={isAdmin ? 'An administrator code is required.' : 'Register to start managing cases and evidence.'}
      footer={<>
        <span>Already registered? <Link to={isAdmin ? '/admin/login' : '/login'}>Sign in</Link></span>
        <span>{isAdmin ? <Link to="/signup">Investigator sign up</Link> : <Link to="/admin/signup">Administrator sign up</Link>}</span>
      </>}>
      <form onSubmit={submit} noValidate className="form">
        {apiErr && <div className="alert alert-error" role="alert">{apiErr}</div>}
        <label className="field"><span className="field-label">Full name</span><Input icon={User} placeholder="Full name" value={f.full_name} error={errors.full_name} onChange={set('full_name')} /></label>
        <label className="field"><span className="field-label">Email</span><Input icon={Mail} type="email" placeholder="you@agency.gov.pk" value={f.email} error={errors.email} onChange={set('email')} /></label>
        <label className="field"><span className="field-label">Badge number <small>(optional)</small></span><Input icon={BadgeCheck} placeholder="e.g. FIA-2041" value={f.badge_number} error={errors.badge_number} onChange={set('badge_number')} /></label>
        <div className="grid-2">
          <label className="field"><span className="field-label">Password</span>
            <Input icon={Lock} type={show ? 'text' : 'password'} autoComplete="new-password" placeholder="Min. 8 characters" value={f.password} error={errors.password} onChange={set('password')}
              right={<button type="button" className="icon-btn sm" onClick={() => setShow((s) => !s)} aria-label="Toggle password">{show ? <EyeOff size={16} /> : <Eye size={16} />}</button>} />
          </label>
          <label className="field"><span className="field-label">Confirm password</span><Input icon={Lock} type={show ? 'text' : 'password'} autoComplete="new-password" placeholder="Repeat password" value={f.confirm} error={errors.confirm} onChange={set('confirm')} /></label>
        </div>
        {isAdmin && <label className="field"><span className="field-label">Administrator code</span><Input icon={KeyRound} type="password" placeholder="Provided by the system owner" value={f.admin_code} error={errors.admin_code} onChange={set('admin_code')} /></label>}
        <button className="btn btn-dark lg block" disabled={busy}>{busy && <Spinner size={16} />} Create account</button>
      </form>
    </AuthFrame>
  )
}
