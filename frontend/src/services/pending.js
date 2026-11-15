/*
 * MODULE STATUS — which backend capabilities exist today.
 *
 * Verified against backend/app/api/*.py:
 *   analysis.py and reports.py are empty files (and services/ai_analysis.py is empty),
 *   and there are no user-listing or audit-log read routes.
 *
 * The matching pages (AIAnalysis, Reports, admin/Users, admin/AuditLogs) show an
 * "integration pending" panel instead of fake data. When you add those routes, add the
 * calls to services/api.js, build the live UI in the page, and flip the flag here.
 */
export const BACKEND = {
  auth: true,
  cases: true,
  evidence: true,
  integrity: true,
  ledger: true,
  analysis: false, // AI analysis, OCR, findings, risk score
  reports: false, //  report generation + PDF download
  users: false, //    list users / activate / change role
  auditLogs: false, // read audit_logs table (rows are already being written)
}
