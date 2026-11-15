import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Copy, Loader2, X, AlertTriangle, Inbox, Wrench } from 'lucide-react'
import { useToast } from '../../context/ToastContext'
import { label } from '../../utils/format'

export const Spinner = ({ size = 18 }) => <Loader2 size={size} className="spin" />

export const PageLoader = ({ text = 'Loading…' }) => (
  <div className="page-loader"><Spinner size={26} /><span>{text}</span></div>
)

export function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export const EmptyState = ({ icon: Icon = Inbox, title, text, action }) => (
  <div className="empty"><Icon size={34} strokeWidth={1.3} /><h3>{title}</h3>{text && <p>{text}</p>}{action}</div>
)

export const ErrorState = ({ message, onRetry }) => (
  <div className="empty error">
    <AlertTriangle size={34} strokeWidth={1.3} />
    <h3>Could not load data</h3><p>{message}</p>
    {onRetry && <button className="btn btn-outline" onClick={onRetry}>Try again</button>}
  </div>
)

// Colour is reserved for small semantic dots; everything else stays black & white.
const TONE = {
  open: 'info', in_progress: 'warn', under_review: 'warn', closed: 'muted',
  low: 'muted', medium: 'info', high: 'warn', critical: 'danger',
  intact: 'ok', tampered: 'danger', missing: 'danger', ledger_broken: 'danger', pending: 'muted',
  verified: 'ok', mismatch: 'danger', failed: 'danger',
  admin: 'dark', investigator: 'info', active: 'ok', inactive: 'danger',
}
export const Badge = ({ value, text, tone }) => (
  <span className={`badge badge-${tone || TONE[value] || 'muted'}`}><i />{text || label(value)}</span>
)

export const StatCard = ({ icon: Icon, label: l, value, hint, pending }) => (
  <div className={`stat ${pending ? 'stat-pending' : ''}`}>
    <div className="stat-top"><span>{l}</span>{Icon && <Icon size={18} strokeWidth={1.6} />}</div>
    <div className="stat-value">{pending ? '—' : value}</div>
    {hint && <div className="stat-hint">{hint}</div>}
  </div>
)

export function Modal({ open, title, onClose, children, footer, wide }) {
  useEffect(() => {
    if (!open) return
    const h = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', h)
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', h); document.body.style.overflow = '' }
  }, [open, onClose])
  if (!open) return null
  return createPortal(
    <div className="modal-back" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true">
        <div className="modal-head"><h3>{title}</h3><button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>,
    document.body,
  )
}

export function ConfirmDialog({ open, title, message, confirmText = 'Confirm', danger, busy, onConfirm, onClose }) {
  return (
    <Modal open={open} title={title} onClose={onClose}
      footer={<>
        <button className="btn btn-outline" onClick={onClose} disabled={busy}>Cancel</button>
        <button className={`btn ${danger ? 'btn-danger' : 'btn-dark'}`} onClick={onConfirm} disabled={busy}>
          {busy && <Spinner size={14} />}{confirmText}
        </button>
      </>}>
      <p className="muted">{message}</p>
    </Modal>
  )
}

export function Field({ label: l, error, hint, children }) {
  return (
    <label className="field">
      <span className="field-label">{l}</span>
      {children}
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

export function Hash({ value, full }) {
  const toast = useToast()
  if (!value) return <span className="muted">—</span>
  const copy = () => navigator.clipboard?.writeText(value).then(() => toast.success('Hash copied'))
  return (
    <span className="hash" title={value}>
      <code>{full ? value : `${value.slice(0, 14)}…${value.slice(-8)}`}</code>
      <button className="icon-btn sm" onClick={copy} aria-label="Copy hash"><Copy size={13} /></button>
    </span>
  )
}

export function IntegrationPending({ title, needs, children }) {
  return (
    <div className="pending">
      <div className="pending-icon"><Wrench size={20} /></div>
      <div>
        <div className="pending-tag">Backend integration pending</div>
        <h3>{title}</h3>
        <p className="muted">{needs}</p>
        {children}
      </div>
    </div>
  )
}
