import { useCallback, useEffect, useState } from 'react'
import {
  type Me,
  fetchToday,
  fetchTodayReading,
  type Factor,
  type Revelation,
  saveResidence,
  type TodayReading,
  type TodaySky,
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

const timeOf = (iso: string, zone: string) =>
  new Intl.DateTimeFormat('pt-PT', {
    timeZone: zone,
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))

function RevelationOrigin({
  revelation,
  zone,
  since,
}: {
  revelation: Revelation
  zone: string
  since: string
}) {
  const event = revelation.event
  const transit = revelation.transit
  const next = transit?.exact.find((instant) => new Date(instant) >= new Date(since))
  return (
    <>
      {event ? (
        <>
          {describeEvent(event)} <span className="hint">— {when(event.at, zone)}</span>
        </>
      ) : transit ? (
        <>
          {describeTransit(transit)}
          <span className="hint">
            {' '}
            — {transit.applying ? 'a aproximar-se' : 'a afastar-se'}
            {next ? `, exato a ${when(next, zone)}` : ''}
          </span>
        </>
      ) : null}
      {revelation.supporting.map((factor: Factor, index: number) => {
        const description = factor.event
          ? describeEvent(factor.event)
          : factor.transit
            ? describeTransit(factor.transit)
            : null
        return description ? (
          <span className="supporting" key={index}>
            + {description}
          </span>
        ) : null
      })}
    </>
  )
}

function ReadingSkeleton() {
  return (
    <div className="reading-skeleton" aria-busy="true">
      <span className="skeleton" />
      <span className="skeleton" />
      <span className="skeleton" />
    </div>
  )
}

export function Today({ me, onMoved }: { me: Me; onMoved: () => unknown }) {
  const [sky, setSky] = useState<TodaySky | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reading, setReading] = useState<TodayReading | null>(null)
  const [readingError, setReadingError] = useState<string | null>(null)
  const [moving, setMoving] = useState(false)

  const requestToday = useCallback(() => {
    fetchToday()
      .then((result) => {
        setError(null)
        setSky(result)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
    fetchTodayReading()
      .then((result) => {
        setReadingError(null)
        setReading(result)
      })
      .catch((err: unknown) => setReadingError(err instanceof Error ? err.message : String(err)))
  }, [])

  useEffect(() => {
    requestToday()
  }, [me.residence_zone, me.residence_name, requestToday])

  const nextUnlock = sky?.revelations.find((slot) => slot.revelation === null)?.unlocks_at
  useEffect(() => {
    if (!sky || !nextUnlock) return
    const serverOffset = new Date(sky.now).getTime() - Date.now()
    const delay = new Date(nextUnlock).getTime() - (Date.now() + serverOffset)
    const timeout = window.setTimeout(requestToday, Math.max(0, delay))
    return () => window.clearTimeout(timeout)
  }, [sky, nextUnlock, requestToday])

  if (error) return <p role="alert">{error}</p>
  if (!sky) return <p>A ler o céu de hoje…</p>
  const zone = sky.zone
  return (
    <section className="card today" aria-label="Hoje">
      <h2>A energia do dia</h2>
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
            const name = describePlace(place).slice(0, 200)
            const sameResidence = place.zone === me.residence_zone && name === me.residence_name
            void saveResidence(name, place.zone)
              .then(() => {
                setReading(null)
                setMoving(false)
                onMoved()
                if (sameResidence) requestToday()
              })
              .catch((err: unknown) =>
                setError(err instanceof Error ? err.message : String(err)),
              )
          }}
        />
      )}
      {reading?.theme && <p className="day-theme">{reading.theme}</p>}
      {!reading && !readingError && <p className="day-theme skeleton" aria-busy="true" />}
      {sky.revelations.length === 0 ? (
        <p>Hoje o céu está calmo sobre o teu mapa.</p>
      ) : (
        <div className="revelations">
          {sky.revelations.map((slot, index) => {
            const revelation = slot.revelation
            if (!revelation) {
              return (
                <article className="revelation locked" key={index}>
                  <svg
                    viewBox="0 0 24 24"
                    width="24"
                    height="24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <rect x="4" y="10" width="16" height="11" rx="2" />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                  </svg>
                  <p>Abre às {timeOf(slot.unlocks_at, zone)}</p>
                </article>
              )
            }
            const text = reading?.revelations[index]
            return (
              <article className="revelation" key={index}>
                <p className="origin">
                  <RevelationOrigin revelation={revelation} zone={zone} since={sky.day_starts} />
                </p>
                {text ? (
                  <>
                    <h3>{text.title}</h3>
                    {text.text
                      .split(/\n{2,}/)
                      .filter(Boolean)
                      .map((paragraph, paragraphIndex) => (
                        <p key={paragraphIndex}>{paragraph}</p>
                      ))}
                    <p className="question">{text.question}</p>
                  </>
                ) : readingError ? null : (
                  <ReadingSkeleton />
                )}
              </article>
            )
          })}
        </div>
      )}
      {sky.tomorrow && (
        <article className="secret">
          <h3>O segredo de amanhã</h3>
          <p className="hint">Uma descoberta está a aproximar-se</p>
          <p className="origin">
            <RevelationOrigin revelation={sky.tomorrow} zone={zone} since={sky.day_starts} />
          </p>
          {reading?.tomorrow && <p>{reading.tomorrow}</p>}
          {!reading && !readingError && <ReadingSkeleton />}
        </article>
      )}
      {readingError && <p className="hint">{readingError}</p>}
      {sky.upcoming.length > 0 && (
        <>
          <h3>O que se aproxima</h3>
          <ul>
            {sky.upcoming.slice(0, 5).map((transit, index) => (
              <li key={index}>
                {describeTransit(transit)}
                <span className="hint">
                  {' '}
                  — a partir de {transit.starts && when(transit.starts, zone)}
                </span>
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
              .filter((event) => event.kind !== 'house_ingress')
              .slice(0, 8)
              .map((event, index) => (
                <li key={index}>
                  {describeEvent(event)}
                  <span className="hint"> — {when(event.at, zone)}</span>
                </li>
              ))}
          </ul>
        </>
      )}
      {reading?.note && <p className="hint">{reading.note}</p>}
    </section>
  )
}
