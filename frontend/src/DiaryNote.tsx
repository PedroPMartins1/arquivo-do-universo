import { useEffect, useState } from 'react'
import { fetchReflections, type Reflection } from './api'
import { ReflectionEditor } from './Reflection'

export function DiaryNote({ zone, onSaved }: { zone: string; onSaved: () => void }) {
  const parts = new Intl.DateTimeFormat('en', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
  const part = (type: string) => parts.find((item) => item.type === type)!.value
  const day = `${part('year')}-${part('month')}-${part('day')}`
  const [note, setNote] = useState<Reflection | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetchReflections(day).then((items) => {
      if (active) setNote(items.find((item) => item.slot === null) ?? null)
    }).catch(() => {
      if (active) setError('Não foi possível abrir a tua nota. Tenta novamente antes de escrever.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [day, attempt])

  return <article className="note diary-compose" aria-label="Escrever no diário">
    <p className="eyebrow">Hoje</p>
    <h3>Como estás a viver este dia?</h3>
    {loading && <p role="status">A abrir a tua nota…</p>}
    {error && <><p role="alert">{error}</p><button type="button" className="secondary" onClick={() => setAttempt((value) => value + 1)}>Tentar novamente</button></>}
    {!loading && !error && <ReflectionEditor day={day} slot={null} initial={note} label="Nota do dia" hint="Um pensamento, um acontecimento ou algo que queres recordar." onChange={(reflection) => { setNote(reflection); onSaved() }} />}
  </article>
}
