// Central frontend configuration.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Backend default is MAX_UPLOAD_SIZE_MB = 50 (backend/app/config.py). Keep in sync.
export const MAX_UPLOAD_MB = 50

// The backend stores crime_type as a free string; these are the scope-document categories.
export const CRIME_TYPES = ['Cyberbullying', 'Phishing', 'Ransomware', 'Fraud', 'Data Theft']

export const CASE_STATUSES = ['open', 'in_progress', 'under_review', 'closed']
export const CASE_PRIORITIES = ['low', 'medium', 'high', 'critical']

// The contact form on the landing page opens the visitor's mail client (no backend endpoint exists for it).
export const CONTACT_EMAIL = 'forensicore.fyp@example.com' // TODO: replace with your real project e-mail

export const BRAND = 'ForensiCore'
