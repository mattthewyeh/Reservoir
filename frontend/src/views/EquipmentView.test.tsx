import {render, screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {beforeEach, describe, expect, it, vi} from 'vitest'

import * as api from '../api'
import type {Equipment} from '../types'
import {EquipmentView} from './EquipmentView'


vi.mock('../api', () => ({
  createReservation: vi.fn(),
  getAvailableEquipment: vi.fn(),
  getEquipment: vi.fn(),
}))

const equipment: Equipment[] = [
  {
    id: 1,
    name: 'Cinema camera',
    description: 'Records high-resolution video',
    is_active: true,
    created_at: '2026-09-15T12:00:00Z',
  },
  {
    id: 2,
    name: 'Cordless drill',
    description: 'Useful for woodworking projects',
    is_active: true,
    created_at: '2026-09-15T12:00:00Z',
  },
]

describe('EquipmentView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.getEquipment).mockResolvedValue(equipment)
  })

  it('filters equipment by name or description', async () => {
    const user = userEvent.setup()

    render(<EquipmentView token="member-token" />)

    expect(await screen.findByText('Cinema camera')).toBeInTheDocument()
    expect(screen.getByText('Cordless drill')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Search equipment'), 'woodworking')

    expect(screen.queryByText('Cinema camera')).not.toBeInTheDocument()
    expect(screen.getByText('Cordless drill')).toBeInTheDocument()
    expect(screen.getByText('1 of 2 items')).toBeInTheDocument()
  })
})
