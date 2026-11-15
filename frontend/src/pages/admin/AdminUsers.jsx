import { Users, UserCheck, UserX, Shield } from 'lucide-react'
import { PageHeader, IntegrationPending, EmptyState } from '../../components/ui/ui'

export default function AdminUsers() {
  return (
    <>
      <PageHeader eyebrow="Administration" title="User management" subtitle="Investigator accounts, roles and activation status." />
      <IntegrationPending title="User management API is not available yet"
        needs="The backend can create accounts (signup) and lets admins reassign cases by user ID, but it has no route to list users, change roles or activate/deactivate accounts. Add those routes and then build the table here." />
      <section className="card">
        <div className="toolbar tight"><button className="btn btn-dark" disabled><Users size={15} /> Create account</button><button className="btn btn-outline" disabled><Shield size={15} /> Assign role</button>
          <button className="btn btn-outline" disabled><UserCheck size={15} /> Activate</button><button className="btn btn-outline" disabled><UserX size={15} /> Deactivate</button></div>
        <EmptyState icon={Users} title="No user data available" text="New investigators and admins can already register from the sign-up pages." />
      </section>
    </>
  )
}
