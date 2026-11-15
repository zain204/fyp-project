import { authApi } from './api'
import { tokenStore } from './tokenStore'

export async function login({ email, password, role, remember }) {
  const data = await authApi.login({ email, password, role })
  tokenStore.set(data.access_token, data.user, remember)
  return data.user
}
export const signup = (payload) => authApi.signup(payload)
export const logout = () => tokenStore.clear()
