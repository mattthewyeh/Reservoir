import {useState} from 'react'

import {Logo} from './Logo'
import {AdminView} from '../views/AdminView'
import {EquipmentView} from '../views/EquipmentView'
import {ReservationsView} from '../views/ReservationsView'
import type {User} from '../types'
import {initials} from '../utils'


type View = 'equipment' | 'reservations' | 'admin'

interface DashboardProps {
  token: string
  user: User
  onLogout: () => void
}

const navigation: {id: View; label: string}[] = [
  {id: 'equipment', label: 'Find equipment'},
  {id: 'reservations', label: 'My reservations'},
]

export function Dashboard({token, user, onLogout}: DashboardProps) {
  const [view, setView] = useState<View>('equipment')
  const visibleNavigation =
    user.role === 'admin'
      ? [...navigation, {id: 'admin' as const, label: 'Admin'}]
      : navigation

  return (
    <div className="app-shell">
      <header className="app-header">
        <Logo />
        <nav className="main-nav" aria-label="Primary navigation">
          {visibleNavigation.map((item) => (
            <button
              type="button"
              key={item.id}
              className={view === item.id ? 'active' : ''}
              onClick={() => setView(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="user-menu">
          <span className="avatar">{initials(user.full_name)}</span>
          <span className="user-copy">
            <strong>{user.full_name}</strong>
            <small>{user.role === 'admin' ? 'Administrator' : 'Member'}</small>
          </span>
          <button type="button" className="text-button" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="mobile-nav" aria-label="Mobile navigation">
        {visibleNavigation.map((item) => (
          <button
            type="button"
            key={item.id}
            className={view === item.id ? 'active' : ''}
            onClick={() => setView(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <main className="dashboard-main">
        {view === 'equipment' && <EquipmentView token={token} />}
        {view === 'reservations' && <ReservationsView token={token} />}
        {view === 'admin' && user.role === 'admin' && <AdminView token={token} />}
      </main>
    </div>
  )
}
