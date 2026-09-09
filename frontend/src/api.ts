import type {
  Equipment,
  EquipmentInput,
  RegistrationInput,
  Reservation,
  ReservationInput,
  TimeRange,
  User,
} from './types'


const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

interface ValidationErrorItem {
  msg?: string
}

interface ErrorBody {
  detail?: string | ValidationErrorItem[]
}

interface TokenResponse {
  access_token: string
  token_type: string
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function errorMessage(body: ErrorBody | null, fallback: string): string {
  if (typeof body?.detail === 'string') {
    return body.detail
  }

  if (Array.isArray(body?.detail)) {
    const messages = body.detail
      .map((item) => item.msg)
      .filter((message): message is string => Boolean(message))

    if (messages.length > 0) {
      return messages.join('. ')
    }
  }

  return fallback
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers)

  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_URL}${path}`, {...options, headers})

  if (!response.ok) {
    let body: ErrorBody | null = null

    try {
      body = (await response.json()) as ErrorBody
    } catch {
      body = null
    }

    throw new ApiError(
      errorMessage(body, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return (await response.json()) as T
}

export function register(input: RegistrationInput): Promise<User> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams({username: email, password})
  const response = await request<TokenResponse>('/auth/token', {
    method: 'POST',
    body: form,
  })
  return response.access_token
}

export function getCurrentUser(token: string): Promise<User> {
  return request<User>('/auth/me', {}, token)
}

export function getEquipment(): Promise<Equipment[]> {
  return request<Equipment[]>('/equipment')
}

export function getAvailableEquipment(range: TimeRange): Promise<Equipment[]> {
  const query = new URLSearchParams({
    starts_at: range.starts_at,
    ends_at: range.ends_at,
  })
  return request<Equipment[]>(`/equipment/availability?${query.toString()}`)
}

export function createReservation(
  input: ReservationInput,
  token: string,
): Promise<Reservation> {
  return request<Reservation>(
    '/reservations',
    {method: 'POST', body: JSON.stringify(input)},
    token,
  )
}

export function getReservations(token: string): Promise<Reservation[]> {
  return request<Reservation[]>('/reservations', {}, token)
}

export function cancelReservation(
  reservationId: number,
  token: string,
): Promise<Reservation> {
  return request<Reservation>(
    `/reservations/${reservationId}/cancel`,
    {method: 'POST'},
    token,
  )
}

export function getAdminEquipment(token: string): Promise<Equipment[]> {
  return request<Equipment[]>('/admin/equipment', {}, token)
}

export function createEquipment(
  input: EquipmentInput,
  token: string,
): Promise<Equipment> {
  return request<Equipment>(
    '/equipment',
    {method: 'POST', body: JSON.stringify(input)},
    token,
  )
}

export function updateEquipment(
  equipmentId: number,
  input: Partial<EquipmentInput>,
  token: string,
): Promise<Equipment> {
  return request<Equipment>(
    `/equipment/${equipmentId}`,
    {method: 'PATCH', body: JSON.stringify(input)},
    token,
  )
}

export function getAdminReservations(token: string): Promise<Reservation[]> {
  return request<Reservation[]>('/admin/reservations', {}, token)
}

export function cancelAdminReservation(
  reservationId: number,
  token: string,
): Promise<Reservation> {
  return request<Reservation>(
    `/admin/reservations/${reservationId}/cancel`,
    {method: 'POST'},
    token,
  )
}
