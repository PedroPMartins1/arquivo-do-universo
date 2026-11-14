import { useEffect, useState } from 'react'
import {
  type DailySky,
  fetchToday,
  fetchTodayReading,
  type Me,
  type Revelation,
  saveResidence,
  type TodayReading,
} from './api'
import { describeEvent, describePlace, describeTransit } from './labels'
import { PlaceSearch } from './PlaceSearch'

const when = (iso: string, zone: string) =>
  new Intl.DateTimeFormat('pt-PT', {
    timeZone: zone,
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))

function RevelationText({
  revelation,
  zone,
  since,
}: {
  revelation: Revelation
  zone: string
  since: string
}) {
  if (revelation.event) {
    const e = revelation.event
    return (
      <>
        <strong>{describeEvent(e)}</strong>
        <span className="hint"> — {when(e.at, zone)}</span>
      </>
    )
  }
  const t = revelation.transit
  if (!t) return null
  const next = t.exact.find((x) => new Date(x) >= new Date(since))
  return (
    <>
      <strong>{describeTransit(t)}</strong>
      <span className="hint">
        {' '}
        — {t.applying ? 'a aproximar-se' : 'a afastar-se'}
        {next ? `, exato a ${when(next, zone)}` : ''}
      </span>
    </>
  )
}

export function Today({ me, onMoved }: { me: Me; onMoved: () => unknown }) {
  const [sky, setSky] = useState<DailySky | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reading, setReading] = useState<TodayReading | null>(null)
  const [readingError, setReadingError] = useState<string | null>(null)
  const [moving, setMoving] = useState(false)

  useEffect(() => {
    fetchToday()
      .then((s) => {
        setError(null)
        setSky(s)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
    fetchTodayReading()
      .then((result) => {
        setReadingError(null)
        setReading(result)
      })
      .catch((err: unknown) =>
        setReadingError(err instanceof Error ? err.message : String(err)),
      )
  }, [me.residence_zone, me.residence_name])

  if (error) return <p role="alert">{error}</p>
  if (!sky) return <p>A ler o céu de hoje…</p>
  const zone = sky.zone
  return (
    <section className="card" aria-label="Hoje">
      <h2>Revelações do dia</h2>
      <p className="hint">
        {new Intl.DateTimeFormat('pt-PT', { dateStyle: 'full', timeZone: 'UTC' }).format(
          new Date(`${sky.date}T12:00:00Z`),
        )}{' '}
        · {me.residence_name ?? zone}{' '}
        <button type="button" className="link" onClick={() => setMoving(!moving)}>
          Mudar o local onde vives
        </button>
      </p>
      {moving && (
        <PlaceSearch
          onSelect={(place) => {
            if (!place) return
            void saveResidence(describePlace(place).slice(0, 200), place.zone)
              .then(() => {
                setReading(null)
                setMoving(false)
                onMoved()
              })
              .catch((err: unknown) =>
                setError(err instanceof Error ? err.message : String(err)),
              )
          }}
        />
      )}
      {sky.revelations.length === 0 ? (
        <p>Hoje o céu está calmo sobre o teu mapa.</p>
      ) : (
        <ol className="revelations">
          {sky.revelations.map((r, i) => (
            <li key={i}>
              <RevelationText revelation={r} zone={zone} since={sky.day_starts} />
              {reading?.revelations[i] && (
                <p className="reading-text">{reading.revelations[i]}</p>
              )}
            </li>
          ))}
        </ol>
      )}
      {sky.tomorrow && (
        <>
          <h3>O segredo de amanhã</h3>
          <p>
            <RevelationText revelation={sky.tomorrow} zone={zone} since={sky.day_starts} />
          </p>
          {reading?.tomorrow && <p className="reading-text">{reading.tomorrow}</p>}
        </>
      )}
      {readingError && <p className="hint">{readingError}</p>}
      {!reading && !readingError && <p className="hint">A interpretar o céu…</p>}
      {reading?.note && <p className="hint">{reading.note}</p>}
      {sky.upcoming.length > 0 && (
        <>
          <h3>O que se aproxima</h3>
          <ul>
            {sky.upcoming.slice(0, 5).map((t, i) => (
              <li key={i}>
                {describeTransit(t)}
                <span className="hint"> — a partir de {t.starts && when(t.starts, zone)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      {sky.events.length > 0 && (
        <>
          <h3>O céu nos próximos dias</h3>
          <ul>
            {sky.events
              .filter((e) => e.kind !== 'house_ingress')
              .slice(0, 8)
              .map((e, i) => (
                <li key={i}>
                  {describeEvent(e)}
                  <span className="hint"> — {when(e.at, zone)}</span>
                </li>
              ))}
          </ul>
        </>
      )}
    </section>
  )
}
