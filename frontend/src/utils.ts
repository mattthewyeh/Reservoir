export function formatDateTime(timestamp: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(timestamp))
}

export function toUtcIso(localDateTime: string): string {
  return new Date(localDateTime).toISOString()
}

export function toLocalInputValue(date: Date): string {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

export function defaultReservationRange(): {startsAt: string; endsAt: string} {
  const startsAt = new Date()
  startsAt.setDate(startsAt.getDate() + 1)
  startsAt.setMinutes(0, 0, 0)
  startsAt.setHours(Math.max(startsAt.getHours(), 9))

  const endsAt = new Date(startsAt)
  endsAt.setHours(endsAt.getHours() + 2)

  return {
    startsAt: toLocalInputValue(startsAt),
    endsAt: toLocalInputValue(endsAt),
  }
}

export function initials(fullName: string): string {
  return fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong'
}
