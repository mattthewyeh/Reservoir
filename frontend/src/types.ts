export type UserRole = 'user' | 'admin'
export type ReservationStatus = 'confirmed' | 'cancelled'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  created_at: string
}

export interface Equipment {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
}

export interface Reservation {
  id: number
  user_id: number
  equipment_id: number
  starts_at: string
  ends_at: string
  status: ReservationStatus
  created_at: string
}

export interface RegistrationInput {
  email: string
  full_name: string
  password: string
}

export interface EquipmentInput {
  name: string
  description: string | null
  is_active?: boolean
}

export interface ReservationInput {
  equipment_id: number
  starts_at: string
  ends_at: string
}

export interface TimeRange {
  starts_at: string
  ends_at: string
}
