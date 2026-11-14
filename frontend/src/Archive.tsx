import { useCallback, useEffect, useState } from 'react'
import { fetchArchive, fetchArchiveDay, type ArchiveDay, type ArchiveDayDetail, type Reflection } from './api'
import { RevelationOrigin } from './Today'
import { ReflectionEditor } from './Reflection'

const longDate = (day: string) =>
  new Intl.DateTimeFormat('pt-PT', { dateStyle: 'full', timeZone: 'UTC' }).format(
    new Date(`${day}T12:00:00Z`),
  )

const monthDate = (day: string) =>
  new Intl.DateTimeFormat('pt-PT', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(
    new Date(`${day}T12:00:00Z`),
  )

const timeOf = (instant: string, zone: string) =>
  new Intl.DateTimeFormat('pt-PT', { timeZone: zone, hour: '2-digit', minute: '2-digit' }).format(
    new Date(instant),
  )

const messageOf = (error: unknown) => (error instanceof Error ? error.message : String(error))

export function Archive({ zone }: { zone: string }) {
  const [page, setPage] = useState<{ days: ArchiveDay[]; next_before: string | null } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDay, setSelectedDay] = useState<string | null>(null)
  const [detail, setDetail] = useState<ArchiveDayDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const loadPage = useCallback(async (before?: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchArchive(before)
      setPage((current) =>
        before && current
          ? { ...result, days: [...current.days, ...result.days] }
          : result,
      )
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadPage()
  }, [loadPage])

  async function openDay(day: string) {
    setSelectedDay(day)
    setDetail(null)
    setDetailError(null)
    setDetailLoading(true)
    try {
      setDetail(await fetchArchiveDay(day))
    } catch (err) {
      setDetailError(messageOf(err))
    } finally {
      setDetailLoading(false)
    }
  }

  function updateReflection(reflection: Reflection | null, slot: number | null) {
    setDetail((current) => {
      if (!current) return current
      const reflections = current.reflections.filter((item) => item.slot !== slot)
      if (reflection) reflections.push(reflection)
      reflections.sort((first, second) => (first.slot ?? 5) - (second.slot ?? 5))
      return { ...current, reflections }
    })
  }

  if (selectedDay) {
    return (
      <section className="card archive-detail" aria-label="Detalhe do Arquivo">
        <button
          type="button"
          className="link"
          onClick={() => {
            setSelectedDay(null)
            setDetail(null)
            void loadPage()
          }}
        >
          ← Voltar ao Arquivo
        </button>
        {detailLoading && <p>A abrir o dia…</p>}
        {detailError && <p role="alert">{detailError}</p>}
        {detail && (
          <>
            <h2>{longDate(detail.date)}</h2>
            {detail.theme && <p className="day-theme">{detail.theme}</p>}
            <div className="revelations">
              {detail.revelations.map((slot, index) =>
                slot.reading === null ? (
                  <article className="revelation locked" key={index}>
                    <p>Abre às {timeOf(slot.unlocks_at, zone)}</p>
                  </article>
                ) : (
                  <article className="revelation" key={index}>
                    {slot.origin && (
                      <p className="origin">
                        <RevelationOrigin
                          revelation={slot.origin}
                          zone={zone}
                          since={`${detail.date}T00:00:00Z`}
                        />
                      </p>
                    )}
                    <h3>{slot.reading.title}</h3>
                    {slot.reading.text
                      .split(/\n{2,}/)
                      .filter(Boolean)
                      .map((paragraph, paragraphIndex) => (
                        <p key={paragraphIndex}>{paragraph}</p>
                      ))}
                    <p className="question">{slot.reading.question}</p>
                    <ReflectionEditor
                      day={detail.date}
                      slot={index}
                      initial={detail.reflections.find((item) => item.slot === index) ?? null}
                      label="A tua reflexão"
                      onChange={(reflection) => updateReflection(reflection, index)}
                    />
                  </article>
                ),
              )}
            </div>
            <article className="note">
              <h3>Nota do dia</h3>
              <ReflectionEditor
                day={detail.date}
                slot={null}
                initial={detail.reflections.find((item) => item.slot === null) ?? null}
                label="Nota do dia"
                hint="O que aconteceu hoje, o que sentiste ou o que decidiste fazer."
                onChange={(reflection) => updateReflection(reflection, null)}
              />
            </article>
            {detail.note && <p className="hint">{detail.note}</p>}
          </>
        )}
      </section>
    )
  }

  const groups = new Map<string, ArchiveDay[]>()
  for (const day of page?.days ?? []) {
    const month = monthDate(day.date)
    groups.set(month, [...(groups.get(month) ?? []), day])
  }

  return (
    <section className="card archive" aria-label="Arquivo">
      <h2>Arquivo</h2>
      {error && <p role="alert">{error}</p>}
      {loading && <p>A abrir o Arquivo…</p>}
      {!loading && !error && page?.days.length === 0 && (
        <p>O teu Arquivo começa hoje: as leituras e reflexões de cada dia vão ficando guardadas aqui.</p>
      )}
      {[...groups].map(([month, days]) => (
        <section className="archive-month" key={month}>
          <h3>{month}</h3>
          <ul className="archive-days">
            {days.map((day) => (
              <li key={day.date}>
                <button type="button" className="archive-day" onClick={() => void openDay(day.date)}>
                  <span>{longDate(day.date)}</span>
                  {day.theme && <strong>{day.theme}</strong>}
                  <span className="hint">
                    {day.reflection_count}{' '}
                    {day.reflection_count === 1 ? 'reflexão' : 'reflexões'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {page?.next_before && (
        <button type="button" disabled={loading} onClick={() => void loadPage(page.next_before ?? undefined)}>
          Ver mais
        </button>
      )}
    </section>
  )
}
