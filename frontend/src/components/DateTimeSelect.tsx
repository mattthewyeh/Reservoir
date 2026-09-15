import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'

interface DateTimeSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  min?: string
}

interface DropdownOption {
  value: string
  label: string
  disabled?: boolean
}

interface DropdownListProps {
  label: string
  value: string
  options: DropdownOption[]
  isOpen: boolean
  onToggle: () => void
  onClose: () => void
  onSelect: (value: string) => void
}

interface CalendarDropdownProps {
  label: string
  value: string
  options: DropdownOption[]
  isOpen: boolean
  onToggle: () => void
  onClose: () => void
  onSelect: (value: string) => void
}

const DATE_OPTION_COUNT = 60
const HALF_HOUR_IN_MS = 30 * 60 * 1000

function localDateValue(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function dateLabel(value: string): string {
  const [year, month, day] = value.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  const today = localDateValue(new Date())
  const prefix = value === today ? 'Today · ' : ''

  return `${prefix}${new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  }).format(date)}`
}

function timeLabel(value: string): string {
  const [hours, minutes] = value.split(':').map(Number)
  const date = new Date(2000, 0, 1, hours, minutes)

  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

function dateButtonLabel(value: string): string {
  const [year, month, day] = value.split('-').map(Number)
  const date = new Date(year, month - 1, day)

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function parseLocalDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function monthIndex(date: Date): number {
  return date.getFullYear() * 12 + date.getMonth()
}

function firstDayOfMonth(value: string): Date {
  const date = parseLocalDate(value)
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

function calendarDays(month: Date): Array<string | null> {
  const year = month.getFullYear()
  const monthIndexValue = month.getMonth()
  const firstWeekday = new Date(year, monthIndexValue, 1).getDay()
  const numberOfDays = new Date(year, monthIndexValue + 1, 0).getDate()

  return [
    ...Array.from({length: firstWeekday}, () => null),
    ...Array.from({length: numberOfDays}, (_, index) =>
      localDateValue(new Date(year, monthIndexValue, index + 1)),
    ),
  ]
}

function dateOptions(selectedDate: string): string[] {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const options = Array.from({length: DATE_OPTION_COUNT}, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() + index)
    return localDateValue(date)
  })

  if (selectedDate && !options.includes(selectedDate)) {
    options.push(selectedDate)
    options.sort()
  }

  return options
}

const timeOptions = Array.from({length: 48}, (_, index) => {
  const totalMinutes = index * 30
  const hours = String(Math.floor(totalMinutes / 60)).padStart(2, '0')
  const minutes = String(totalMinutes % 60).padStart(2, '0')
  return `${hours}:${minutes}`
})

function CalendarDropdown({
  label,
  value,
  options,
  isOpen,
  onToggle,
  onClose,
  onSelect,
}: CalendarDropdownProps) {
  const calendarId = useId()
  const triggerRef = useRef<HTMLButtonElement>(null)
  const [displayedMonth, setDisplayedMonth] = useState(() =>
    firstDayOfMonth(value),
  )
  const enabledDates = options.filter((option) => !option.disabled)
  const firstDate = parseLocalDate(enabledDates[0]?.value ?? value)
  const lastDate = parseLocalDate(enabledDates.at(-1)?.value ?? value)
  const availableDates = new Set(
    enabledDates.map((option) => option.value),
  )
  const days = calendarDays(displayedMonth)
  const today = localDateValue(new Date())

  function moveMonth(offset: number) {
    setDisplayedMonth(
      new Date(
        displayedMonth.getFullYear(),
        displayedMonth.getMonth() + offset,
        1,
      ),
    )
  }

  function handleToggle() {
    if (!isOpen) {
      setDisplayedMonth(firstDayOfMonth(value))
    }
    onToggle()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.preventDefault()
      onClose()
      triggerRef.current?.focus()
    }
  }

  return (
    <div
      className="datetime-control datetime-control-date"
      onKeyDown={handleKeyDown}
    >
      <span className="datetime-control-label">Date</span>
      <button
        ref={triggerRef}
        type="button"
        className={`datetime-trigger${isOpen ? ' open' : ''}`}
        aria-label={label}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-controls={isOpen ? calendarId : undefined}
        onClick={handleToggle}
      >
        <span>{dateButtonLabel(value)}</span>
        <span className="datetime-chevron" aria-hidden="true">⌄</span>
      </button>
      {isOpen && (
        <div
          className="calendar-popover"
          id={calendarId}
          role="dialog"
          aria-label={`${label} calendar`}
        >
          <div className="calendar-header">
            <strong>
              {new Intl.DateTimeFormat(undefined, {
                month: 'long',
                year: 'numeric',
              }).format(displayedMonth)}
            </strong>
            <div className="calendar-navigation">
              <button
                type="button"
                aria-label="Previous month"
                disabled={monthIndex(displayedMonth) <= monthIndex(firstDate)}
                onClick={() => moveMonth(-1)}
              >
                ←
              </button>
              <button
                type="button"
                aria-label="Next month"
                disabled={monthIndex(displayedMonth) >= monthIndex(lastDate)}
                onClick={() => moveMonth(1)}
              >
                →
              </button>
            </div>
          </div>
          <div className="calendar-weekdays" aria-hidden="true">
            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((weekday, index) => (
              <span key={`${weekday}-${index}`}>{weekday}</span>
            ))}
          </div>
          <div className="calendar-grid">
            {days.map((date, index) =>
              date ? (
                <button
                  key={date}
                  type="button"
                  className="calendar-day"
                  aria-label={new Intl.DateTimeFormat(undefined, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  }).format(parseLocalDate(date))}
                  aria-current={date === today ? 'date' : undefined}
                  aria-pressed={date === value}
                  disabled={!availableDates.has(date)}
                  onClick={() => {
                    onSelect(date)
                    onClose()
                    triggerRef.current?.focus()
                  }}
                >
                  {parseLocalDate(date).getDate()}
                </button>
              ) : (
                <span key={`blank-${index}`} aria-hidden="true" />
              ),
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function DropdownList({
  label,
  value,
  options,
  isOpen,
  onToggle,
  onClose,
  onSelect,
}: DropdownListProps) {
  const listId = useId()
  const triggerRef = useRef<HTMLButtonElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const selectedOption = options.find((option) => option.value === value)

  useEffect(() => {
    if (!isOpen) {
      return
    }

    const list = listRef.current
    const selectedButton = list?.querySelector<HTMLButtonElement>(
      '[aria-selected="true"]',
    )
    if (list && selectedButton) {
      list.scrollTop =
        selectedButton.offsetTop -
        (list.clientHeight - selectedButton.offsetHeight) / 2
    }
  }, [isOpen])

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.preventDefault()
      onClose()
      triggerRef.current?.focus()
      return
    }

    if (!isOpen && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault()
      onToggle()
      return
    }

    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      return
    }

    event.preventDefault()
    const enabledOptions = Array.from(
      listRef.current?.querySelectorAll<HTMLButtonElement>(
        '.datetime-option:not(:disabled)',
      ) ?? [],
    )
    const currentIndex = enabledOptions.findIndex(
      (option) => option === document.activeElement,
    )
    const selectedIndex = enabledOptions.findIndex(
      (option) => option.getAttribute('aria-selected') === 'true',
    )
    let nextIndex = currentIndex

    if (event.key === 'Home') {
      nextIndex = 0
    } else if (event.key === 'End') {
      nextIndex = enabledOptions.length - 1
    } else if (event.key === 'ArrowDown') {
      nextIndex = Math.min(
        (currentIndex === -1 ? selectedIndex : currentIndex) + 1,
        enabledOptions.length - 1,
      )
    } else {
      nextIndex = Math.max(
        (currentIndex === -1 ? selectedIndex : currentIndex) - 1,
        0,
      )
    }

    enabledOptions[nextIndex]?.focus()
  }

  return (
    <div className="datetime-control datetime-control-time" onKeyDown={handleKeyDown}>
      <span className="datetime-control-label">Time</span>
      <button
        ref={triggerRef}
        type="button"
        className={`datetime-trigger${isOpen ? ' open' : ''}`}
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listId : undefined}
        onClick={onToggle}
      >
        <span>{selectedOption?.label}</span>
        <span className="datetime-chevron" aria-hidden="true">⌄</span>
      </button>
      {isOpen && (
        <div
          ref={listRef}
          className="datetime-menu datetime-menu-time"
          id={listId}
          role="listbox"
          aria-label={`${label} options`}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              className="datetime-option"
              role="option"
              aria-selected={option.value === value}
              disabled={option.disabled}
              tabIndex={option.value === value ? 0 : -1}
              onClick={() => {
                onSelect(option.value)
                onClose()
                triggerRef.current?.focus()
              }}
            >
              <span>{option.label}</span>
              {option.value === value && (
                <span className="datetime-check" aria-hidden="true">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function DateTimeSelect({
  label,
  value,
  onChange,
  min,
}: DateTimeSelectProps) {
  const labelId = useId()
  const fieldRef = useRef<HTMLDivElement>(null)
  const [openMenu, setOpenMenu] = useState<'date' | 'time' | null>(null)
  const [selectedDate, selectedTime] = value.split('T')
  const dates = useMemo(() => dateOptions(selectedDate), [selectedDate])
  const minDate = min?.slice(0, 10)
  const minTime = min?.slice(11, 16)

  useEffect(() => {
    if (!openMenu) {
      return
    }

    function closeOnOutsideClick(event: PointerEvent) {
      if (!fieldRef.current?.contains(event.target as Node)) {
        setOpenMenu(null)
      }
    }

    document.addEventListener('pointerdown', closeOnOutsideClick)
    return () => document.removeEventListener('pointerdown', closeOnOutsideClick)
  }, [openMenu])

  function updateValue(nextDate: string, nextTime: string) {
    let nextValue = `${nextDate}T${nextTime}`

    if (min && nextValue <= min) {
      const adjustedDate = new Date(new Date(min).getTime() + HALF_HOUR_IN_MS)
      const adjustedDateValue = localDateValue(adjustedDate)
      const adjustedTimeValue = adjustedDate.toTimeString().slice(0, 5)
      nextValue = `${adjustedDateValue}T${adjustedTimeValue}`
    }

    onChange(nextValue)
  }

  const dateListOptions = dates.map((date) => ({
    value: date,
    label: dateLabel(date),
    disabled: Boolean(minDate && date < minDate),
  }))
  const timeListOptions = timeOptions.map((time) => ({
    value: time,
    label: timeLabel(time),
    disabled: Boolean(
      minDate === selectedDate && minTime && time <= minTime,
    ),
  }))

  return (
    <div
      ref={fieldRef}
      className="datetime-field"
      role="group"
      aria-labelledby={labelId}
    >
      <span className="datetime-label" id={labelId}>{label}</span>
      <div className="datetime-selects">
        <CalendarDropdown
          label={`${label} date`}
          value={selectedDate}
          options={dateListOptions}
          isOpen={openMenu === 'date'}
          onToggle={() => setOpenMenu(openMenu === 'date' ? null : 'date')}
          onClose={() => setOpenMenu(null)}
          onSelect={(date) => updateValue(date, selectedTime)}
        />
        <DropdownList
          label={`${label} time`}
          value={selectedTime}
          options={timeListOptions}
          isOpen={openMenu === 'time'}
          onToggle={() => setOpenMenu(openMenu === 'time' ? null : 'time')}
          onClose={() => setOpenMenu(null)}
          onSelect={(time) => updateValue(selectedDate, time)}
        />
      </div>
    </div>
  )
}
