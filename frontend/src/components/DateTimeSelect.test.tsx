import {render, screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {expect, it, vi} from 'vitest'

import {DateTimeSelect} from './DateTimeSelect'

it('offers ordinary date and time lists', () => {
  render(
    <DateTimeSelect
      label="Start"
      value="2026-09-10T09:00"
      onChange={() => undefined}
    />,
  )

  expect(screen.getByRole('combobox', {name: 'Start date'})).toBeInTheDocument()
  expect(screen.getByRole('combobox', {name: 'Start time'})).toBeInTheDocument()
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

  expect(screen.getByRole('option', {name: '10:00 AM'})).toBeDisabled()
  expect(screen.getByRole('option', {name: '10:30 AM'})).toBeDisabled()

  await user.selectOptions(screen.getByRole('combobox', {name: 'End time'}), '11:30')

  expect(onChange).toHaveBeenCalledWith('2026-09-10T11:30')
})
