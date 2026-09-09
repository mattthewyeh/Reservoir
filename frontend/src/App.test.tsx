import {render, screen, waitFor, within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'

import App from './App'
import * as api from './api'
import type {User} from './types'


vi.mock('./api', () => ({
  cancelAdminReservation: vi.fn(),
  cancelReservation: vi.fn(),
  createEquipment: vi.fn(),
  createReservation: vi.fn(),
  getAdminEquipment: vi.fn(),
  getAdminReservations: vi.fn(),
  getAvailableEquipment: vi.fn(),
  getCurrentUser: vi.fn(),
  getEquipment: vi.fn(),
  getReservations: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  updateEquipment: vi.fn(),
}))

const member: User = {
  id: 1,
  email: 'member@example.com',
  full_name: 'Example Member',
  role: 'user',
  created_at: '2026-09-08T12:00:00Z',
}

const admin: User = {
  ...member,
  id: 2,
  email: 'admin@example.com',
  full_name: 'Example Admin',
  role: 'admin',
}

function prepareDashboardData() {
  vi.mocked(api.getEquipment).mockResolvedValue([])
  vi.mocked(api.getReservations).mockResolvedValue([])
  vi.mocked(api.getAdminEquipment).mockResolvedValue([])
  vi.mocked(api.getAdminReservations).mockResolvedValue([])
}

describe('Reservoir app', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    prepareDashboardData()
  })

  it('signs in and stores the access token', async () => {
    const user = userEvent.setup()
    vi.mocked(api.login).mockResolvedValue('member-token')
    vi.mocked(api.getCurrentUser).mockResolvedValue(member)

    render(<App />)

    await user.type(screen.getByLabelText('Email address'), member.email)
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.keyboard('{Enter}')

    expect(await screen.findByText('Find your next tool.')).toBeInTheDocument()
    expect(api.login).toHaveBeenCalledWith(member.email, 'password123')
    expect(localStorage.getItem('reservoir.accessToken')).toBe('member-token')
    expect(screen.queryByRole('button', {name: 'Admin'})).not.toBeInTheDocument()
  })

  it('registers a new user and signs in automatically', async () => {
    const user = userEvent.setup()
    vi.mocked(api.register).mockResolvedValue(member)
    vi.mocked(api.login).mockResolvedValue('new-member-token')
    vi.mocked(api.getCurrentUser).mockResolvedValue(member)

    render(<App />)

    await user.click(screen.getByRole('button', {name: 'Register'}))
    await user.type(screen.getByLabelText('Full name'), member.full_name)
    await user.type(screen.getByLabelText('Email address'), member.email)
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', {name: 'Create account'}))

    expect(await screen.findByText('Find your next tool.')).toBeInTheDocument()
    expect(api.register).toHaveBeenCalledWith({
      full_name: member.full_name,
      email: member.email,
      password: 'password123',
    })
    expect(api.login).toHaveBeenCalledWith(member.email, 'password123')
  })

  it('restores an admin session and shows admin navigation', async () => {
    localStorage.setItem('reservoir.accessToken', 'admin-token')
    vi.mocked(api.getCurrentUser).mockResolvedValue(admin)

    render(<App />)

    expect(screen.getByLabelText('Restoring your session')).toBeInTheDocument()
    expect(await screen.findByText('Find your next tool.')).toBeInTheDocument()

    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalledWith('admin-token')
    })
    const primaryNavigation = screen.getByRole('navigation', {name: 'Primary navigation'})
    expect(within(primaryNavigation).getByRole('button', {name: 'Admin'})).toBeInTheDocument()
  })
})
