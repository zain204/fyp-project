import { casesApi, evidenceApi } from '../services/api'
import { useFetch } from './useFetch'

// The backend has no "list all evidence" route, so we read the user's cases and
// then each case's evidence (/cases/ then /evidence/case/{id}).
export async function loadAllEvidence() {
  const cases = await casesApi.list({ limit: 200 })
  const lists = await Promise.all(
    cases.map((c) =>
      evidenceApi.byCase(c.id).then((items) => items.map((e) => ({ ...e, case: c }))).catch(() => []),
    ),
  )
  const evidence = lists.flat().sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at))
  return { cases, evidence }
}

export const useAllEvidence = (deps = []) => useFetch(loadAllEvidence, deps)
