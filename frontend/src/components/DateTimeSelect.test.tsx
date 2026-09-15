import {render, screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {expect, it, vi} from 'vitest'

import {DateTimeSelect} from './DateTimeSelect'

it('opens a calendar for dates and a styled list for times', async () => {
  const user = userEvent.setup()

  render(
    <DateTimeSelect
      label="Start"
      value="2026-09-10T09:00"
      onChange={() => undefined}
    />,
  )

  expect(screen.getByRole('button', {name: 'Start date'})).toBeInTheDocument()
  expect(screen.getByRole('button', {name: 'Start time'})).toBeInTheDocument()

  await user.click(screen.getByRole('button', {name: 'Start date'}))

  expect(screen.getByRole('dialog', {name: 'Start date calendar'})).toBeInTheDocument()
  expect(screen.getByText('September 2026')).toBeInTheDocument()
  expect(screen.getByRole('button', {pressed: true})).toHaveAccessibleName(
    'Thursday, September 10, 2026',
  )

  await user.click(screen.getByRole('button', {name: 'Start time'}))

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(screen.getByRole('listbox', {name: 'Start time options'})).toBeInTheDocument()
  expect(screen.getByRole('option', {name: '9:00 AM'})).toBeInTheDocument()
  expect(screen.getByRole('option', {name: '9:30 AM'})).toBeInTheDocument()
})

it('disables end times that do not follow the start time', async () => {
  const user = userEvent.setup()
  const onChange = vi.fn()

  render(
    <DateTimeSelect
      label="End"
      value="2026-09-10T11:00"
      min="2026-09-10T10:30"
      onChange={onChange}
    />,
  )

  await user.click(screen.getByRole('button', {name: 'End time'}))

  expect(screen.getByRole('option', {name: '10:00 AM'})).toBeDisabled()
  expect(screen.getByRole('option', {name: '10:30 AM'})).toBeDisabled()

  await user.click(screen.getByRole('option', {name: '11:30 AM'}))

  expect(onChange).toHaveBeenCalledWith('2026-09-10T11:30')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})
