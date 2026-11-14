import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { type Me, type Place, type TodaySky } from './api'
import { describeEvent } from './labels'
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
        focus: 'jupiter',
        supporting: [
          {
            weight: 2.5,
            transit: {
              body: 'mars',
              natal_point: 'midheaven',
              kind: 'trine',
              starts: null,
              ends: null,
              exact: [],
              orb: null,
              applying: null,
              natal_house: 10,
              weight: 2.5,
            },
            event: null,
          },
        ],
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
      other_body: null,
      aspect: null,
      contacts: [],
      weight: 3.75,
    },
    focus: null,
    supporting: [],
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
  Promise.resolve(
    url.includes('/me/reading/today')
      ? json(TODAY_READING)
      : url.includes('/me/reflections/')
        ? json([])
        : json(SKY),
  )

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
    expect(screen.getByText('+ Marte em trígono com Meio do Céu natal')).toBeInTheDocument()
  })

  it('mostra a reflexão só na revelação aberta e guarda a resposta e a nota', async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes('/me/reflections/') && init?.method === 'PUT') {
        const slot = url.includes('/note') ? null : 0
        return Promise.resolve(
          json({
            day: SKY.date,
            slot,
            question: slot === null ? null : TODAY_READING.revelations[0]?.question,
            body: JSON.parse(String(init.body)).body,
            created_at: '2026-11-16T12:00:00Z',
            updated_at: '2026-11-16T12:00:00Z',
            provenance: 'user_reported',
          }),
        )
      }
      return responseFor(url)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<Today me={ME} onMoved={() => undefined} />)
    const openArticle = (await screen.findByText('Um convite à pausa')).closest('article')
    expect(openArticle).not.toBeNull()
    const reflection = within(openArticle as HTMLElement)
    const textarea = await reflection.findByLabelText('A tua reflexão')
    fireEvent.change(textarea, {
      target: { value: 'Quero reservar tempo para esta ideia.' },
    })
    fireEvent.click(reflection.getByRole('button', { name: 'Guardar' }))
    expect(await reflection.findByText('Guardada')).toBeInTheDocument()
    expect(reflection.getByText('Quero reservar tempo para esta ideia.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/me/reflections/${SKY.date}/revelations/0`,
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ body: 'Quero reservar tempo para esta ideia.' }),
      }),
    )

    const lockedArticle = document.querySelector('article.revelation.locked')
    expect(lockedArticle?.querySelector('.reflection-editor')).toBeNull()
    const noteArticle = document.querySelector('article.note')
    expect(noteArticle).not.toBeNull()
    const note = within(noteArticle as HTMLElement)
    fireEvent.change(note.getByLabelText('Nota do dia'), {
      target: { value: 'Hoje escolhi avançar com calma.' },
    })
    fireEvent.click(note.getByRole('button', { name: 'Guardar' }))
    expect(await note.findByText('Guardada')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/me/reflections/${SKY.date}/note`,
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ body: 'Hoje escolhi avançar com calma.' }),
      }),
    )
  })

  it('descreve um aspeto entre planetas no céu', () => {
    expect(
      describeEvent({
        kind: 'sky_aspect',
        body: 'venus',
        sign: null,
        natal_house: null,
        eclipse_type: null,
        other_body: 'mars',
        aspect: 'trine',
      }),
    ).toBe('Vénus em trígono com Marte no céu')
    expect(
      describeEvent({
        kind: 'moon_sign_ingress',
        body: 'moon',
        sign: 'taurus',
        natal_house: 2,
        eclipse_type: null,
      }),
    ).toBe('Lua entra em Touro')
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
            : url.includes('/me/reflections/')
              ? json([])
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
