import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { type DailySky, type Me, type Place } from './api'
import { Today } from './Today'

vi.mock('./PlaceSearch', () => ({
  PlaceSearch: ({ onSelect }: { onSelect: (place: Place | null) => void }) => (
    <button
      type="button"
      onClick={() =>
        onSelect({
          id: 1,
          name: 'Sintra',
          region: null,
          country_code: 'PT',
          latitude: 38.8029,
          longitude: -9.3817,
          zone: 'Europe/Lisbon',
        })
      }
    >
      Selecionar Sintra
    </button>
  ),
}))

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })

const ME: Me = {
  id: '1',
  email: 'ana@example.org',
  display_name: 'Ana',
  residence_name: 'Lisboa',
  residence_zone: 'Europe/Lisbon',
}

const SKY: DailySky = {
  date: '2026-11-12',
  zone: 'Europe/Lisbon',
  day_starts: '2026-11-11T23:00:00Z',
  revelations: [
    {
      weight: 6,
      transit: {
        body: 'saturn',
        natal_point: 'jupiter',
        kind: 'square',
        starts: null,
        ends: null,
        exact: ['2026-11-12T21:58:53Z'],
        orb: 0.02,
        applying: true,
        natal_house: 8,
        weight: 6,
      },
      event: null,
    },
  ],
  tomorrow: null,
  active: [],
  upcoming: [],
  events: [],
}

const TODAY_READING = {
  date: SKY.date,
  revelations: [],
  tomorrow: null,
  model: 'fake-claude',
  prompt_version: 'test',
  generated_at: '2026-11-12T00:00:00Z',
  epistemic_class: 'interpretation' as const,
  note: 'Interpretação simbólica gerada por IA.',
}

const responseFor = (url: string) =>
  Promise.resolve(url.includes('/me/reading/today') ? json(TODAY_READING) : json(SKY))

const todayCalls = (fetchMock: ReturnType<typeof vi.fn>) =>
  fetchMock.mock.calls.filter(([url]) => String(url).includes('/me/today')).length

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Today', () => {
  it('mostra as revelações do dia', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => responseFor(url)))
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByRole('heading', { name: 'Revelações do dia' })).toBeInTheDocument()
    expect(screen.getByText(/Saturno em quadratura com Júpiter natal/)).toBeInTheDocument()
  })

  it('mostra a interpretação por baixo da revelação calculada', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        Promise.resolve(
          url.includes('/me/reading/today')
            ? json({
                date: SKY.date,
                revelations: ['Este trânsito convida-te a observar os teus limites.'],
                tomorrow: null,
                model: 'fake-claude',
                prompt_version: 'test',
                generated_at: '2026-11-12T00:00:00Z',
                epistemic_class: 'interpretation',
                note: 'Interpretação simbólica gerada por IA.',
              })
            : json(SKY),
        ),
      ),
    )
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(
      await screen.findByText('Este trânsito convida-te a observar os teus limites.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Interpretação simbólica gerada por IA.')).toBeInTheDocument()
  })

  it('mantém o céu calculado e mostra o erro quando a leitura falha', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        Promise.resolve(
          url.includes('/me/reading/today')
            ? json({ detail: 'a interpretação não está disponível neste momento' }, 503)
            : json(SKY),
        ),
      ),
    )
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(
      await screen.findByText(/Saturno em quadratura com Júpiter natal/),
    ).toBeInTheDocument()
    expect(
      await screen.findByText('a interpretação não está disponível neste momento'),
    ).toBeInTheDocument()
  })

  it('volta a pedir o céu quando a residência muda, mesmo dentro do mesmo fuso', async () => {
    const fetchMock = vi.fn((url: string) => responseFor(url))
    vi.stubGlobal('fetch', fetchMock)
    const { rerender } = render(<Today me={ME} onMoved={() => undefined} />)
    await screen.findByRole('heading', { name: 'Revelações do dia' })
    expect(todayCalls(fetchMock)).toBe(1)
    rerender(<Today me={{ ...ME, residence_name: 'Sintra' }} onMoved={() => undefined} />)
    await waitFor(() => expect(todayCalls(fetchMock)).toBe(2))
  })

  it('limpa o erro quando uma leitura posterior tem sucesso', async () => {
    let skyCalls = 0
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/me/reading/today')) return Promise.resolve(json(TODAY_READING))
      skyCalls += 1
      return Promise.resolve(skyCalls === 1 ? json({ detail: 'falhou' }, 500) : json(SKY))
    })
    vi.stubGlobal('fetch', fetchMock)
    const { rerender } = render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('falhou')
    rerender(<Today me={{ ...ME, residence_zone: 'Atlantic/Azores' }} onMoved={() => undefined} />)
    expect(
      await screen.findByRole('heading', { name: 'Revelações do dia' }),
    ).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('limpa a interpretação anterior quando a residência muda', async () => {
    const previousReading = {
      ...TODAY_READING,
      revelations: ['Interpretação do local anterior'],
    }
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        Promise.resolve(
          url.includes('/me/reading/today')
            ? json(previousReading)
            : url.includes('/me/residence')
              ? json(ME)
              : json(SKY),
        ),
      ),
    )
    const onMoved = vi.fn()
    render(<Today me={ME} onMoved={onMoved} />)
    expect(await screen.findByText('Interpretação do local anterior')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Mudar o local onde vives' }))
    fireEvent.click(screen.getByRole('button', { name: 'Selecionar Sintra' }))

    await waitFor(() => expect(onMoved).toHaveBeenCalledOnce())
    expect(screen.queryByText('Interpretação do local anterior')).not.toBeInTheDocument()
    expect(screen.getByText('A interpretar o céu…')).toBeInTheDocument()
  })
})
