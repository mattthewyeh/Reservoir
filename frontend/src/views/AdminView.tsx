import {useEffect, useState, type FormEvent} from 'react'

import {
  cancelAdminReservation,
  createEquipment,
  getAdminEquipment,
  getAdminReservations,
  updateEquipment,
} from '../api'
import type {Equipment, Reservation} from '../types'
import {formatDateTime, messageFrom} from '../utils'


interface AdminViewProps {
  token: string
}

interface EquipmentEditorProps {
  equipment: Equipment
  token: string
  onSaved: (equipment: Equipment) => void
}

function EquipmentEditor({equipment, token, onSaved}: EquipmentEditorProps) {
  const [name, setName] = useState(equipment.name)
  const [description, setDescription] = useState(equipment.description ?? '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  async function saveEquipment() {
    setError('')
    setIsSaving(true)

    try {
      const updated = await updateEquipment(
        equipment.id,
        {name, description: description || null},
        token,
      )
      onSaved(updated)
    } catch (saveError) {
      setError(messageFrom(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  async function toggleActive() {
    setError('')
    setIsSaving(true)

    try {
      const updated = await updateEquipment(
        equipment.id,
        {is_active: !equipment.is_active},
        token,
      )
      onSaved(updated)
    } catch (saveError) {
      setError(messageFrom(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <article className="admin-equipment-row">
      <div className="admin-equipment-id">#{equipment.id}</div>
      <label>
        <span>Name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} />
      </label>
      <label className="admin-description-field">
        <span>Description</span>
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Optional description"
        />
      </label>
      <span className={`status-pill ${equipment.is_active ? 'confirmed' : 'cancelled'}`}>
        {equipment.is_active ? 'active' : 'inactive'}
      </span>
      <div className="admin-row-actions">
        <button
          type="button"
          className="button button-small button-secondary"
          onClick={saveEquipment}
          disabled={isSaving}
        >
          Save
        </button>
        <button
          type="button"
          className="button button-small button-ghost"
          onClick={toggleActive}
          disabled={isSaving}
        >
          {equipment.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </div>
      {error && <small className="inline-error">{error}</small>}
    </article>
  )
}

export function AdminView({token}: AdminViewProps) {
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  async function loadAdminData() {
    setError('')
    setIsLoading(true)

    try {
      const [equipmentData, reservationData] = await Promise.all([
        getAdminEquipment(token),
        getAdminReservations(token),
      ])
      setEquipment(equipmentData)
      setReservations(reservationData)
    } catch (loadError) {
      setError(messageFrom(loadError))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let isActive = true

    Promise.all([getAdminEquipment(token), getAdminReservations(token)])
      .then(([equipmentData, reservationData]) => {
        if (isActive) {
          setEquipment(equipmentData)
          setReservations(reservationData)
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

  function replaceEquipment(updated: Equipment) {
    setEquipment((current) =>
      current
        .map((item) => (item.id === updated.id ? updated : item))
        .sort((first, second) => first.name.localeCompare(second.name)),
    )
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsCreating(true)

    try {
      const created = await createEquipment(
        {name, description: description || null},
        token,
      )
      setEquipment((current) =>
        [...current, created].sort((first, second) =>
          first.name.localeCompare(second.name),
        ),
      )
      setName('')
      setDescription('')
    } catch (createError) {
      setError(messageFrom(createError))
    } finally {
      setIsCreating(false)
    }
  }

  async function handleAdminCancel(reservationId: number) {
    setError('')
    setCancellingId(reservationId)

    try {
      const updated = await cancelAdminReservation(reservationId, token)
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
    <div className="page-stack admin-page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Operations</p>
          <h1>Admin workspace</h1>
          <p>Keep inventory accurate and resolve schedule changes.</p>
        </div>
        <button type="button" className="button button-secondary" onClick={loadAdminData}>
          Refresh all
        </button>
      </section>

      {error && <div className="form-alert page-alert">{error}</div>}

      <section className="admin-section">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">Inventory</p>
            <h2>Equipment management</h2>
          </div>
          <span className="count-chip">{equipment.length} total</span>
        </div>

        <form className="create-equipment-form" onSubmit={handleCreate}>
          <label>
            Equipment name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Cinema camera"
              maxLength={200}
              required
            />
          </label>
          <label>
            Description
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="What should members know?"
              maxLength={2000}
            />
          </label>
          <button className="button button-primary" disabled={isCreating}>
            {isCreating ? 'Adding…' : 'Add equipment'}
          </button>
        </form>

        {isLoading ? (
          <div className="loading-block">Loading inventory…</div>
        ) : (
          <div className="admin-equipment-list">
            {equipment.map((item) => (
              <EquipmentEditor
                key={item.id}
                equipment={item}
                token={token}
                onSaved={replaceEquipment}
              />
            ))}
          </div>
        )}
      </section>

      <section className="admin-section">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">All users</p>
            <h2>Reservation oversight</h2>
          </div>
          <span className="count-chip">{reservations.length} records</span>
        </div>

        <div className="admin-reservation-table">
          <div className="admin-table-head">
            <span>Reservation</span>
            <span>Member</span>
            <span>Schedule</span>
            <span>Status</span>
            <span>Action</span>
          </div>
          {reservations.map((reservation) => (
            <div className="admin-table-row" key={reservation.id}>
              <span>
                <strong>
                  {equipmentNames.get(reservation.equipment_id) ??
                    `Equipment #${reservation.equipment_id}`}
                </strong>
                <small>#{reservation.id}</small>
              </span>
              <span>Member #{reservation.user_id}</span>
              <span>
                {formatDateTime(reservation.starts_at)}
                <small>to {formatDateTime(reservation.ends_at)}</small>
              </span>
              <span>
                <span className={`status-pill ${reservation.status}`}>
                  {reservation.status}
                </span>
              </span>
              <span>
                {reservation.status === 'confirmed' && (
                  <button
                    type="button"
                    className="button button-small button-danger-ghost"
                    onClick={() => handleAdminCancel(reservation.id)}
                    disabled={cancellingId === reservation.id}
                  >
                    {cancellingId === reservation.id ? 'Cancelling…' : 'Cancel'}
                  </button>
                )}
              </span>
            </div>
          ))}
          {!isLoading && reservations.length === 0 && (
            <div className="empty-table">No reservation records yet.</div>
          )}
        </div>
      </section>
    </div>
  )
}
