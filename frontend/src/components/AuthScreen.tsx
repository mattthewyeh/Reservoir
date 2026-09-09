import {useState, type FormEvent} from 'react'

import {Logo} from './Logo'
import {messageFrom} from '../utils'


interface AuthScreenProps {
  onLogin: (email: string, password: string) => Promise<void>
  onRegister: (input: {
    full_name: string
    email: string
    password: string
  }) => Promise<void>
}

type AuthMode = 'login' | 'register'

export function AuthScreen({onLogin, onRegister}: AuthScreenProps) {
  const [mode, setMode] = useState<AuthMode>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      if (mode === 'register') {
        await onRegister({full_name: fullName, email, password})
      } else {
        await onLogin(email, password)
      }
    } catch (submitError) {
      setError(messageFrom(submitError))
    } finally {
      setIsSubmitting(false)
    }
  }

  function selectMode(nextMode: AuthMode) {
    setMode(nextMode)
    setError('')
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Logo />
        <div className="hero-copy">
          <p className="eyebrow">Shared gear, thoughtfully scheduled</p>
          <h1>Make room for the work that matters.</h1>
          <p className="hero-lede">
            Find equipment, reserve a clear time window, and keep your team
            moving without double-bookings or spreadsheet detective work.
          </p>
          <div className="hero-proof" aria-label="Reservoir benefits">
            <div>
              <strong>One view</strong>
              <span>for every shared item</span>
            </div>
            <div>
              <strong>Clear windows</strong>
              <span>with live availability</span>
            </div>
            <div>
              <strong>No collisions</strong>
              <span>protected by the database</span>
            </div>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <span className="orbit-card orbit-card-camera">CAM</span>
          <span className="orbit-card orbit-card-audio">AUD</span>
          <span className="orbit-card orbit-card-light">LGT</span>
          <span className="orbit-line" />
        </div>
      </section>

      <section className="auth-panel-wrap">
        <div className="auth-panel">
          <p className="panel-kicker">Welcome to Reservoir</p>
          <h2>{mode === 'login' ? 'Sign in to continue' : 'Create your account'}</h2>
          <p className="panel-intro">
            {mode === 'login'
              ? 'Your next reservation is a few clicks away.'
              : 'Start reserving shared equipment in minutes.'}
          </p>

          <div className="segmented-control" aria-label="Authentication mode">
            <button
              type="button"
              className={mode === 'login' ? 'active' : ''}
              onClick={() => selectMode('login')}
            >
              Sign in
            </button>
            <button
              type="button"
              className={mode === 'register' ? 'active' : ''}
              onClick={() => selectMode('register')}
            >
              Register
            </button>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {mode === 'register' && (
              <label>
                Full name
                <input
                  name="fullName"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  autoComplete="name"
                  placeholder="Alex Morgan"
                  minLength={1}
                  maxLength={200}
                  required
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder="At least 8 characters"
                minLength={8}
                maxLength={128}
                required
              />
            </label>

            {error && <div className="form-alert">{error}</div>}

            <button className="button button-primary button-full" disabled={isSubmitting}>
              {isSubmitting
                ? 'One moment…'
                : mode === 'login'
                  ? 'Sign in'
                  : 'Create account'}
            </button>
          </form>

          <p className="auth-footnote">
            Secure access tokens expire after 30 minutes.
          </p>
        </div>
      </section>
    </main>
  )
}
