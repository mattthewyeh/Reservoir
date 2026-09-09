import {useEffect, useState} from 'react'

import {cancelReservation, getEquipment, getReservations} from '../api'
import type {Equipment, Reservation} from '../types'
import {formatDateTime, messageFrom} from '../utils'


interface ReservationsViewProps {
  token: string
}

export function ReservationsView({token}: ReservationsViewProps) {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [currentTime] = useState(() => Date.now())

  async function loadReservations() {
    setError('')
    setIsLoading(true)

    try {
      const [reservationData, equipmentData] = await Promise.all([
        getReservations(token),
        getEquipment(),
      ])
      setReservations(reservationData)
      setEquipment(equipmentData)
    } catch (loadError) {
      setError(messageFrom(loadError))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let isActive = true

    Promise.all([getReservations(token), getEquipment()])
      .then(([reservationData, equipmentData]) => {
        if (isActive) {
          setReservations(reservationData)
          setEquipment(equipmentData)
        }
      })
      .catch((loadError) => {
        if (isActive) {
          setError(messageFrom(loadError))
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [token])

  async function handleCancel(reservationId: number) {
    setError('')
    setCancellingId(reservationId)

    try {
      const updated = await cancelReservation(reservationId, token)
      setReservations((current) =>
        current.map((reservation) =>
          reservation.id === updated.id ? updated : reservation,
        ),
      )
    } catch (cancelError) {
      setError(messageFrom(cancelError))
    } finally {
      setCancellingId(null)
    }
  }

  const equipmentNames = new Map(equipment.map((item) => [item.id, item.name]))

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Your schedule</p>
          <h1>My reservations</h1>
          <p>A complete timeline of your confirmed and cancelled bookings.</p>
        </div>
        <button type="button" className="button button-secondary" onClick={loadReservations}>
          Refresh
        </button>
      </section>

      {error && <div className="form-alert page-alert">{error}</div>}

      {isLoading ? (
        <div className="loading-block">Loading your reservations…</div>
      ) : reservations.length === 0 ? (
        <div className="empty-state large">
          <span>—</span>
          <h3>Your schedule is clear.</h3>
          <p>Visit Find equipment when you are ready to book something.</p>
        </div>
      ) : (
        <div className="reservation-list">
          {reservations.map((reservation) => {
            const canCancel =
              reservation.status === 'confirmed' &&
              new Date(reservation.starts_at).getTime() > currentTime

            return (
              <article className="reservation-row" key={reservation.id}>
                <div className="reservation-date">
                  <strong>
                    {new Intl.DateTimeFormat(undefined, {month: 'short'}).format(
                      new Date(reservation.starts_at),
                    )}
                  </strong>
                  <span>
                    {new Intl.DateTimeFormat(undefined, {day: 'numeric'}).format(
                      new Date(reservation.starts_at),
                    )}
                  </span>
                </div>
                <div className="reservation-main">
                  <div className="reservation-title-line">
                    <h3>
                      {equipmentNames.get(reservation.equipment_id) ??
                        `Equipment #${reservation.equipment_id}`}
                    </h3>
                    <span className={`status-pill ${reservation.status}`}>
                      {reservation.status}
                    </span>
                  </div>
                  <p>
                    {formatDateTime(reservation.starts_at)} →{' '}
                    {formatDateTime(reservation.ends_at)}
                  </p>
                  <small>Reservation #{reservation.id}</small>
                </div>
                {canCancel && (
                  <button
                    type="button"
                    className="button button-danger-ghost"
                    onClick={() => handleCancel(reservation.id)}
                    disabled={cancellingId === reservation.id}
                  >
                    {cancellingId === reservation.id ? 'Cancelling…' : 'Cancel'}
                  </button>
                )}
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
