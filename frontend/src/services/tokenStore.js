// Token lives in localStorage when "Remember me" is ticked, otherwise in sessionStorage.
const KEY = 'fc_token'
const USER = 'fc_user'

export const tokenStore = {
  get() {
    return sessionStorage.getItem(KEY) || localStorage.getItem(KEY)
  },
  user() {
    try {
      return JSON.parse(sessionStorage.getItem(USER) || localStorage.getItem(USER) || 'null')
    } catch {
      return null
    }
  },
  set(token, user, remember) {
    this.clear()
    const store = remember ? localStorage : sessionStorage
    store.setItem(KEY, token)
    store.setItem(USER, JSON.stringify(user))
  },
  setUser(user) {
    const store = localStorage.getItem(KEY) ? localStorage : sessionStorage
    store.setItem(USER, JSON.stringify(user))
  },
  clear() {
    ;[sessionStorage, localStorage].forEach((s) => {
      s.removeItem(KEY)
      s.removeItem(USER)
    })
  },
  // JWT "exp" in ms (0 if unreadable)
  expiry() {
    const t = this.get()
    if (!t) return 0
    try {
      return JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).exp * 1000
    } catch {
      return 0
    }
  },
}
