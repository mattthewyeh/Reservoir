import {useEffect, useState, type FormEvent} from 'react'

import {
  createReservation,
  getAvailableEquipment,
  getEquipment,
} from '../api'
import type {Equipment} from '../types'
import {
  defaultReservationRange,
  formatDateTime,
  messageFrom,
  toUtcIso,
} from '../utils'


interface EquipmentViewProps {
  token: string
}

export function EquipmentView({token}: EquipmentViewProps) {
  const defaultRange = defaultReservationRange()
  const [startsAt, setStartsAt] = useState(defaultRange.startsAt)
  const [endsAt, setEndsAt] = useState(defaultRange.endsAt)
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isBooking, setIsBooking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    getEquipment()
      .then(setEquipment)
      .catch((loadError) => setError(messageFrom(loadError)))
      .finally(() => setIsLoading(false))
  }, [])

  async function searchAvailability() {
    setError('')
    setNotice('')
    setIsLoading(true)

    try {
      const availableEquipment = await getAvailableEquipment({
        starts_at: toUtcIso(startsAt),
        ends_at: toUtcIso(endsAt),
      })
      setEquipment(availableEquipment)
      setSelectedEquipment(null)
      setHasSearched(true)
    } catch (searchError) {
      setError(messageFrom(searchError))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await searchAvailability()
  }

  async function handleReservation() {
    if (!selectedEquipment) {
      return
    }

    setError('')
    setNotice('')
    setIsBooking(true)

    try {
      const reservedEquipmentName = selectedEquipment.name
      await createReservation(
        {
          equipment_id: selectedEquipment.id,
          starts_at: toUtcIso(startsAt),
          ends_at: toUtcIso(endsAt),
        },
        token,
      )
      setSelectedEquipment(null)
      await searchAvailability()
      setNotice(`${reservedEquipmentName} is reserved for your selected time.`)
    } catch (reservationError) {
      setError(messageFrom(reservationError))
    } finally {
      setIsBooking(false)
    }
  }

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Equipment library</p>
          <h1>Find your next tool.</h1>
          <p>Choose a time window to see exactly what is free.</p>
        </div>
        <span className="heading-badge">Live availability</span>
      </section>

      <section className="availability-panel">
        <div className="availability-copy">
          <span className="step-number">01</span>
          <div>
            <h2>When do you need it?</h2>
            <p>Times are shown in your local timezone.</p>
          </div>
        </div>
        <form className="availability-form" onSubmit={handleSearch}>
          <label>
            Start
            <input
              type="datetime-local"
              value={startsAt}
              onChange={(event) => setStartsAt(event.target.value)}
              required
            />
          </label>
          <span className="range-arrow" aria-hidden="true">→</span>
          <label>
            End
            <input
              type="datetime-local"
              value={endsAt}
              min={startsAt}
              onChange={(event) => setEndsAt(event.target.value)}
              required
            />
          </label>
          <button className="button button-primary" disabled={isLoading}>
            {isLoading ? 'Checking…' : 'Check availability'}
          </button>
        </form>
      </section>

      {error && <div className="form-alert page-alert">{error}</div>}
      {notice && <div className="success-alert page-alert">{notice}</div>}

      <section className="results-section">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">{hasSearched ? 'Available now' : 'Active inventory'}</p>
            <h2>
              {isLoading
                ? 'Loading equipment…'
                : `${equipment.length} ${equipment.length === 1 ? 'item' : 'items'}`}
            </h2>
          </div>
          {hasSearched && (
            <p className="range-summary">
              {formatDateTime(toUtcIso(startsAt))} — {formatDateTime(toUtcIso(endsAt))}
            </p>
          )}
        </div>

        {!isLoading && equipment.length === 0 && (
          <div className="empty-state">
            <span>0</span>
            <h3>No equipment is free in this window.</h3>
            <p>Try shifting the start or end time to see more options.</p>
          </div>
        )}

        <div className="equipment-grid">
          {equipment.map((item, index) => (
            <article className="equipment-card" key={item.id}>
              <div className={`equipment-visual tone-${index % 4}`}>
                <span>{item.name.slice(0, 3).toUpperCase()}</span>
                <div className="visual-rings" aria-hidden="true" />
              </div>
              <div className="equipment-body">
                <div>
                  <span className="status-dot">Available</span>
                  <h3>{item.name}</h3>
                  <p>{item.description ?? 'Ready for your next project.'}</p>
                </div>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => setSelectedEquipment(item)}
                >
                  Reserve
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      {selectedEquipment && (
        <div className="dialog-backdrop" role="presentation">
          <section className="confirmation-dialog" role="dialog" aria-modal="true">
            <button
              type="button"
              className="dialog-close"
              aria-label="Close reservation confirmation"
              onClick={() => setSelectedEquipment(null)}
            >
              ×
            </button>
            <p className="eyebrow">Confirm reservation</p>
            <h2>{selectedEquipment.name}</h2>
            <div className="booking-summary">
              <div>
                <span>Starts</span>
                <strong>{formatDateTime(toUtcIso(startsAt))}</strong>
              </div>
              <div>
                <span>Ends</span>
                <strong>{formatDateTime(toUtcIso(endsAt))}</strong>
              </div>
            </div>
            <p className="dialog-note">
              Availability is confirmed again when you reserve, protecting the
              schedule if someone else books at the same moment.
            </p>
            <div className="dialog-actions">
              <button
                type="button"
                className="button button-ghost"
                onClick={() => setSelectedEquipment(null)}
              >
                Go back
              </button>
              <button
                type="button"
                className="button button-primary"
                onClick={handleReservation}
                disabled={isBooking}
              >
                {isBooking ? 'Reserving…' : 'Confirm reservation'}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
