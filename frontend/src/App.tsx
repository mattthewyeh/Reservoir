import {useEffect, useState} from 'react'

import {getCurrentUser, login, register} from './api'
import {AuthScreen} from './components/AuthScreen'
import {Dashboard} from './components/Dashboard'
import {Logo} from './components/Logo'
import type {RegistrationInput, User} from './types'


const TOKEN_STORAGE_KEY = 'reservoir.accessToken'

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [isRestoringSession, setIsRestoringSession] = useState(Boolean(token))

  useEffect(() => {
    if (!token) {
      return
    }

    let isActive = true

    getCurrentUser(token)
      .then((currentUser) => {
        if (isActive) {
          setUser(currentUser)
        }
      })
      .catch(() => {
        if (isActive) {
          localStorage.removeItem(TOKEN_STORAGE_KEY)
          setToken(null)
          setUser(null)
        }
      })
      .finally(() => {
        if (isActive) {
          setIsRestoringSession(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [token])

  async function authenticate(email: string, password: string) {
    const accessToken = await login(email, password)
    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
    setIsRestoringSession(true)
    setToken(accessToken)
  }

  async function createAccount(input: RegistrationInput) {
    await register(input)
    await authenticate(input.email, input.password)
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
    setIsRestoringSession(false)
  }

  if (isRestoringSession) {
    return (
      <main className="session-loader">
        <Logo />
        <span className="loader-ring" aria-label="Restoring your session" />
        <p>Opening your equipment workspace…</p>
      </main>
    )
  }

  if (!token || !user) {
    return <AuthScreen onLogin={authenticate} onRegister={createAccount} />
  }

  return <Dashboard token={token} user={user} onLogout={logout} />
}
