import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AppShell from './components/Layout/AppShell'
import PublicLayout from './components/Layout/PublicLayout'
import Landing from './pages/public/Landing'
import InvestigatorLogin from './pages/InvestigatorLogin'
import AdminLogin from './pages/AdminLogin'
import InvestigatorSignup from './pages/InvestigatorSignup'
import AdminSignup from './pages/AdminSignup'
import Dashboard from './pages/Dashboard'
import Cases from './pages/Cases'
import CaseDetail from './pages/CaseDetail'
import Evidence from './pages/Evidence'
import EvidenceDetail from './pages/EvidenceDetail'
import Integrity from './pages/Integrity'
import Custody from './pages/Custody'
import AIAnalysis from './pages/AIAnalysis'
import Reports from './pages/Reports'
import Profile from './pages/Profile'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AuditLogs from './pages/admin/AuditLogs'
import { NotFound, Unauthorized } from './pages/NotFound'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}><Route path="/" element={<Landing />} /></Route>
      <Route path="/login" element={<InvestigatorLogin />} />
      <Route path="/signup" element={<InvestigatorSignup />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/signup" element={<AdminSignup />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="/evidence" element={<Evidence />} />
          <Route path="/evidence/:id" element={<EvidenceDetail />} />
          <Route path="/integrity" element={<Integrity />} />
          <Route path="/custody" element={<Custody />} />
          <Route path="/analysis" element={<AIAnalysis />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute roles={['admin']} />}>
        <Route element={<AppShell />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/audit" element={<AuditLogs />} />
        </Route>
      </Route>

      <Route path="/home" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
