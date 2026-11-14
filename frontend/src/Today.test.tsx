import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { type Me, type Place, type TodaySky } from './api'
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

const SKY: TodaySky = {
  date: '2026-11-16',
  zone: 'Europe/Lisbon',
  day_starts: '2026-11-16T00:00:00Z',
  day_ends: '2026-11-17T00:00:00Z',
  now: '2026-11-16T11:00:00Z',
  revelations: [
    {
      unlocks_at: '2026-11-16T07:00:00Z',
      revelation: {
        weight: 6,
        transit: {
          body: 'saturn',
          natal_point: 'jupiter',
          kind: 'square',
          starts: null,
          ends: null,
          exact: ['2026-11-16T21:58:53Z'],
          orb: 0.02,
          applying: true,
          natal_house: 8,
          weight: 6,
        },
        event: null,
      },
    },
    { unlocks_at: '2026-11-16T13:00:00Z', revelation: null },
  ],
  tomorrow: {
    weight: 3.75,
    transit: null,
    event: {
      kind: 'station_direct',
      at: '2026-11-17T15:53:57Z',
      body: 'mercury',
      sign: 'scorpio',
      natal_house: 3,
      eclipse_type: null,
      contacts: [],
      weight: 3.75,
    },
  },
  active: [],
  upcoming: [],
  events: [],
  calculation: {
    library: 'Swiss Ephemeris',
    library_version: 'test',
    orbs: {},
    aspects: [],
    note: 'Convenções registadas.',
  },
}

const TODAY_READING = {
  date: SKY.date,
  theme: 'Ritmo e estrutura',
  revelations: [
    {
      title: 'Um convite à pausa',
      text: 'Este trânsito convida-te a observar os teus limites.',
      question: 'Que espaço podes criar para ti hoje?',
    },
    null,
  ],
  tomorrow: 'Uma mudança subtil aproxima-se.',
  model: 'fake-claude',
  prompt_version: 'test',
  generated_at: '2026-11-16T00:00:00Z',
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

describe('Hoje', () => {
  it('mostra o conteúdo aberto, a pergunta e o tema do dia', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => responseFor(url)))
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByRole('heading', { name: 'A energia do dia' })).toBeInTheDocument()
    expect(await screen.findByText('Um convite à pausa')).toBeInTheDocument()
    expect(screen.getByText('Este trânsito convida-te a observar os teus limites.')).toBeInTheDocument()
    expect(screen.getByText('Que espaço podes criar para ti hoje?')).toBeInTheDocument()
    expect(screen.getByText('Ritmo e estrutura')).toBeInTheDocument()
  })

  it('não mostra a origem de uma revelação fechada', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => responseFor(url)))
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByText('Abre às 13:00')).toBeInTheDocument()
    const locked = document.querySelector('article.revelation.locked')
    expect(locked).toHaveAttribute('class', 'revelation locked')
    expect(locked?.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
    expect(screen.queryByText(/Vénus entra/)).not.toBeInTheDocument()
  })

  it('mostra esqueletos nas revelações abertas enquanto a leitura carrega', async () => {
    let finishReading: ((response: Response) => void) | undefined
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) =>
        url.includes('/me/reading/today')
          ? new Promise<Response>((resolve) => {
              finishReading = resolve
            })
          : responseFor(url),
      ),
    )
    render(<Today me={ME} onMoved={() => undefined} />)
    await screen.findByText(/Saturno em quadratura com Júpiter natal/)
    const skeleton = document.querySelector('.reading-skeleton[aria-busy="true"]')
    expect(skeleton).not.toBeNull()
    expect(skeleton?.querySelectorAll('.skeleton')).toHaveLength(3)
    finishReading?.(json(TODAY_READING))
    expect(await screen.findByText('Um convite à pausa')).toBeInTheDocument()
  })

  it('mostra o cartão do segredo de amanhã', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => responseFor(url)))
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByRole('heading', { name: 'O segredo de amanhã' })).toBeInTheDocument()
    expect(screen.getByText('Uma descoberta está a aproximar-se')).toBeInTheDocument()
    expect(screen.getByText('Uma mudança subtil aproxima-se.')).toBeInTheDocument()
    expect(document.querySelector('article.secret')).toBeInTheDocument()
  })

  it('mantém a origem calculada e mostra uma única mensagem se a leitura falhar', async () => {
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
    expect(await screen.findByText(/Saturno em quadratura com Júpiter natal/)).toBeInTheDocument()
    expect(await screen.findByText('a interpretação não está disponível neste momento')).toBeInTheDocument()
    expect(screen.getAllByText('a interpretação não está disponível neste momento')).toHaveLength(1)
  })

  it('volta a pedir ambas as rotas quando a residência muda', async () => {
    const fetchMock = vi.fn((url: string) => responseFor(url))
    vi.stubGlobal('fetch', fetchMock)
    const { rerender } = render(<Today me={ME} onMoved={() => undefined} />)
    await screen.findByRole('heading', { name: 'A energia do dia' })
    expect(todayCalls(fetchMock)).toBe(1)
    rerender(<Today me={{ ...ME, residence_name: 'Sintra' }} onMoved={() => undefined} />)
    await waitFor(() => expect(todayCalls(fetchMock)).toBe(2))
    expect(fetchMock.mock.calls.filter(([url]) => String(url).includes('/reading/today'))).toHaveLength(2)
  })

  it('limpa a interpretação antiga e não fica presa ao escolher a mesma residência', async () => {
    let readingCalls = 0
    const previous = {
      ...TODAY_READING,
      revelations: [{ ...TODAY_READING.revelations[0], text: 'Leitura anterior.' }, null],
    }
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/me/reading/today')) {
        readingCalls += 1
        return Promise.resolve(json(readingCalls === 1 ? previous : TODAY_READING))
      }
      if (url.includes('/me/residence')) return Promise.resolve(json(ME))
      return responseFor(url)
    })
    vi.stubGlobal('fetch', fetchMock)
    const onMoved = vi.fn()
    render(<Today me={{ ...ME, residence_name: 'Sintra, Portugal' }} onMoved={onMoved} />)
    expect(await screen.findByText('Leitura anterior.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mudar o local onde vives' }))
    fireEvent.click(screen.getByRole('button', { name: 'Selecionar Sintra' }))
    await waitFor(() => expect(onMoved).toHaveBeenCalledOnce())
    expect(await screen.findByText('Este trânsito convida-te a observar os teus limites.')).toBeInTheDocument()
    expect(screen.queryByText('Leitura anterior.')).not.toBeInTheDocument()
  })
})
