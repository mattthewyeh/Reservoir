import {useId, useMemo} from 'react'

interface DateTimeSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  min?: string
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

export function DateTimeSelect({
  label,
  value,
  onChange,
  min,
}: DateTimeSelectProps) {
  const labelId = useId()
  const [selectedDate, selectedTime] = value.split('T')
  const dates = useMemo(() => dateOptions(selectedDate), [selectedDate])
  const minDate = min?.slice(0, 10)
  const minTime = min?.slice(11, 16)

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

  return (
    <div className="datetime-field" role="group" aria-labelledby={labelId}>
      <span className="datetime-label" id={labelId}>{label}</span>
      <div className="datetime-selects">
        <label>
          <span>Date</span>
          <select
            aria-label={`${label} date`}
            value={selectedDate}
            onChange={(event) => updateValue(event.target.value, selectedTime)}
          >
            {dates.map((date) => (
              <option
                key={date}
                value={date}
                disabled={Boolean(minDate && date < minDate)}
              >
                {dateLabel(date)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Time</span>
          <select
            aria-label={`${label} time`}
            value={selectedTime}
            onChange={(event) => updateValue(selectedDate, event.target.value)}
          >
            {timeOptions.map((time) => (
              <option
                key={time}
                value={time}
                disabled={Boolean(
                  minDate === selectedDate && minTime && time <= minTime,
                )}
              >
                {timeLabel(time)}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
