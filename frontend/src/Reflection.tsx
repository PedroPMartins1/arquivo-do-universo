import { useEffect, useState } from 'react'
import {
  deleteNote,
  deleteRevelationReflection,
  saveNote,
  saveRevelationReflection,
  type Reflection,
} from './api'

export function ReflectionEditor({
  day,
  slot,
  initial,
  label,
  hint,
  onChange,
}: {
  day: string
  slot: number | null
  initial: Reflection | null
  label: string
  hint?: string
  onChange?: (reflection: Reflection | null) => void
}) {
  const [saved, setSaved] = useState<Reflection | null>(initial)
  const [draft, setDraft] = useState(initial?.body ?? '')
  const [editing, setEditing] = useState(initial === null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setSaved(initial)
    setDraft(initial?.body ?? '')
    setEditing(initial === null)
    setError(null)
  }, [day, slot, initial?.body, initial?.updated_at])

  async function save() {
    setBusy(true)
    setError(null)
    try {
      const reflection =
        slot === null
          ? await saveNote(day, draft)
          : await saveRevelationReflection(day, slot, draft)
      setSaved(reflection)
      setDraft(reflection.body)
      setEditing(false)
      onChange?.(reflection)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    setError(null)
    try {
      if (slot === null) await deleteNote(day)
      else await deleteRevelationReflection(day, slot)
      setSaved(null)
      setDraft('')
      setEditing(true)
      onChange?.(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="reflection-editor">
      {hint && <p className="hint">{hint}</p>}
      {error && <p role="alert">{error}</p>}
      {saved && !editing ? (
        <>
          <p className="reflection-body">{saved.body}</p>
          <p className="reflection-status">Guardada</p>
          <div className="reflection-actions">
            <button type="button" className="link" disabled={busy} onClick={() => setEditing(true)}>
              Editar
            </button>
            <button type="button" className="link" disabled={busy} onClick={() => void remove()}>
              Apagar
            </button>
          </div>
        </>
      ) : (
        <>
          <label>
            {label}
            <textarea
              maxLength={5000}
              value={draft}
              disabled={busy}
              onChange={(event) => setDraft(event.currentTarget.value)}
            />
          </label>
          <div className="reflection-actions">
            <button type="button" disabled={busy} onClick={() => void save()}>
              {busy ? 'A guardar…' : 'Guardar'}
            </button>
            {saved && (
              <button
                type="button"
                className="link"
                disabled={busy}
                onClick={() => {
                  setDraft(saved.body)
                  setEditing(false)
                  setError(null)
                }}
              >
                Cancelar
              </button>
            )}
          </div>
        </>
      )}
    </section>
  )
}
