import { useAuthStore } from '../stores/use-auth-store'

export const useAuth = () => {
  const { user, isAuthenticated, login, logout } = useAuthStore()
  
  return {
    user,
    isAuthenticated,
    login,
    logout
  }
}