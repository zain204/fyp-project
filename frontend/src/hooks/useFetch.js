import { useCallback, useEffect, useRef, useState } from 'react'
import { errMsg } from '../services/api'

// Runs an async loader, tracks loading/error, and exposes reload().
export function useFetch(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const ref = useRef(loader)
  ref.current = loader
  const run = useCallback(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    ref.current()
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((e) => alive && setState({ data: null, loading: false, error: errMsg(e) }))
    return () => { alive = false }
  }, [])
  useEffect(() => run(), [run, ...deps]) // eslint-disable-line react-hooks/exhaustive-deps
  return { ...state, reload: run }
}
