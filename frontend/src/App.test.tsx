import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const ME = { id: '1', email: 'ana@example.org', display_name: 'Ana' }
const BIRTH = {
  birth_date: '1993-05-20',
  birth_time: '14:35:00',
  place_name: 'Lisboa',
  latitude: 38.7223,
  longitude: -9.1393,
  zone: 'Europe/Lisbon',
  birth_utc: '1993-05-20T12:35:00Z',
}
const CHART = {
  bodies: [
    {
      body: 'sun',
      longitude: 59.5,
      sign: 'taurus',
      degree_in_sign: 29.5,
      house: 9,
      retrograde: false,
    },
    {
      body: 'moon',
      longitude: 333.25,
      sign: 'pisces',
      degree_in_sign: 3.25,
      house: 6,
      retrograde: false,
    },
  ],
  houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, longitude: i * 30 })),
  angles: { ascendant: 155.2, midheaven: 60, descendant: 335.2, imum_coeli: 240 },
  aspects: [{ first: 'sun', second: 'moon', kind: 'trine', orb: 3.75, applying: false }],
  calculation: { warnings: [] },
}

const SKY = {
  date: '2026-11-12',
  zone: 'Europe/Lisbon',
  day_starts: '2026-11-12T00:00:00Z',
  day_ends: '2026-11-13T00:00:00Z',
  now: '2026-11-12T11:00:00Z',
  revelations: [
    {
      unlocks_at: '2026-11-12T07:00:00Z',
      revelation: {
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
        focus: null,
        supporting: [],
      },
    },
  ],
  tomorrow: {
    weight: 3.75,
    transit: null,
    event: {
      kind: 'station_direct',
      at: '2026-11-13T15:53:57Z',
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

function route(routes: Record<string, () => Response>) {
  return vi.fn((url: string, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${url}`
    return Promise.resolve(routes[key]?.() ?? json({ detail: 'não encontrado' }, 404))
  })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('pede para criar conta quando não há sessão', async () => {
    vi.stubGlobal('fetch', route({ 'GET /api/v1/me': () => json({ detail: 'sessão' }, 401) }))
    render(<App />)
    expect(await screen.findByRole('form', { name: 'Criar conta' })).toBeInTheDocument()
  })

  it('pede os dados de nascimento e depois mostra o mapa', async () => {
    let saved = false
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'GET /api/v1/me/birth': () => (saved ? json(BIRTH) : json({ detail: 'sem dados' }, 404)),
        'PUT /api/v1/me/birth': () => {
          saved = true
          return json({})
        },
        'GET /api/v1/me/chart': () => json(CHART),
        'GET /api/v1/me/today': () => json(SKY),
        'GET /api/v1/places?q=Lisb': () =>
          json({
            results: [
              {
                id: 1,
                name: 'Lisbon',
                region: 'Lisbon',
                country_code: 'PT',
                latitude: 38.7,
                longitude: -9.1,
                zone: 'Europe/Lisbon',
              },
            ],
            attribution: 'GeoNames',
          }),
      }),
    )
    render(<App />)
    const form = await screen.findByRole('form', { name: 'Dados de nascimento' })
    fireEvent.change(screen.getByLabelText('Data de nascimento'), { target: { value: '1993-05-20' } })
    fireEvent.change(screen.getByLabelText('Hora exata'), { target: { value: '14:35' } })
    fireEvent.change(screen.getByLabelText('Local de nascimento'), { target: { value: 'Lisb' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Lisbon, Lisbon, Portugal' }))
    fireEvent.click(screen.getByRole('button', { name: /indicar coordenadas/ }))
    fireEvent.click(screen.getByRole('button', { name: /pelo nome/ }))
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent('Escolhe o local')
    fireEvent.change(screen.getByLabelText('Local de nascimento'), { target: { value: 'Lisb' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Lisbon, Lisbon, Portugal' }))
    fireEvent.submit(form)
    expect(await screen.findByText('Saturno em quadratura com Júpiter natal')).toBeInTheDocument()
    expect(screen.getByText('Mercúrio retoma o movimento direto em Escorpião, na tua casa 3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Perfil' }))
    // Cada signo aparece na roda, no resumo e/ou na tabela.
    expect(await screen.findAllByText('Touro')).toHaveLength(3)
    expect(screen.getAllByText('Peixes')).toHaveLength(3)
    expect(screen.getAllByText('Virgem')).toHaveLength(2)
  })

  it('mostra uma secção da leitura natal', async () => {
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'GET /api/v1/me/birth': () => json(BIRTH),
        'GET /api/v1/me/chart': () => json(CHART),
        'GET /api/v1/me/today': () => json(SKY),
        'GET /api/v1/me/reading/today': () =>
          json({
            date: '2026-11-12',
            theme: 'Tema do dia',
            revelations: [],
            tomorrow: null,
            model: 'fake-claude',
            prompt_version: 'test',
            generated_at: '2026-11-12T00:00:00Z',
            epistemic_class: 'interpretation',
            note: 'Interpretação simbólica gerada por IA.',
          }),
        'GET /api/v1/me/reading/natal': () =>
          json({
            sections: [{ id: 'essencia', title: 'A tua essência', text: 'Uma secção mockada.' }],
            model: 'fake-claude',
            prompt_version: 'test',
            generated_at: '2026-11-12T00:00:00Z',
            epistemic_class: 'interpretation',
            note: 'Interpretação simbólica gerada por IA.',
          }),
      }),
    )
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Perfil' }))
    expect(
      await screen.findByRole('heading', { name: 'A tua leitura' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Uma secção mockada.')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Roda do mapa natal' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Dados de nascimento' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apagar conta' })).toBeInTheDocument()
  })

  it('mostra os cartões Brevemente nos separadores correspondentes', async () => {
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'GET /api/v1/me/birth': () => json(BIRTH),
        'GET /api/v1/me/chart': () => json(CHART),
        'GET /api/v1/me/today': () => json(SKY),
        'GET /api/v1/me/reading/today': () => json({ theme: null, revelations: [], tomorrow: null }),
        'GET /api/v1/me/archive': () => json({ days: [], next_before: null }),
      }),
    )
    render(<App />)
    for (const [tab, text] of [
      ['Explorar', 'Ciclos, eclipses e o calendário do teu céu.'],
      ['Jornada', 'Percursos de evolução e autodesenvolvimento.'],
    ]) {
      fireEvent.click(await screen.findByRole('button', { name: tab }))
      expect(await screen.findByText(text)).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Brevemente' })).toBeInTheDocument()
    }
    fireEvent.click(await screen.findByRole('button', { name: 'Arquivo' }))
    expect(
      await screen.findByText(
        'O teu Arquivo começa hoje: as leituras e reflexões de cada dia vão ficando guardadas aqui.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Arquivo' })).toHaveAttribute('aria-current', 'page')
  })

  it('pede a ocorrência quando a hora aconteceu duas vezes', async () => {
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'PUT /api/v1/me/birth': () => json({ detail: '01:30 aconteceu duas vezes' }, 422),
      }),
    )
    render(<App />)
    const form = await screen.findByRole('form', { name: 'Dados de nascimento' })
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent('Escolhe o local')
    fireEvent.click(screen.getByRole('button', { name: /indicar coordenadas/ }))
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent('duas vezes')
    expect(screen.getByText(/Primeira vez/)).toBeInTheDocument()
  })

  it('permite corrigir os dados quando o mapa não se pode calcular', async () => {
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'GET /api/v1/me/birth': () => json({}),
        'GET /api/v1/me/chart': () => json({ detail: 'Placidus não está definido' }, 422),
      }),
    )
    render(<App />)
    expect(await screen.findByRole('form', { name: 'Dados de nascimento' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Placidus')
    expect(screen.getByText('Sair')).toBeInTheDocument()
  })

  it('permite apagar a conta sem dados de nascimento', async () => {
    let deleted = false
    const fetchMock = route({
      'GET /api/v1/me': () => (deleted ? json({ detail: 'sessão' }, 401) : json(ME)),
      'GET /api/v1/me/birth': () => json({ detail: 'sem dados' }, 404),
      'DELETE /api/v1/me': () => {
        deleted = true
        return new Response(null, { status: 204 })
      },
    })
    const confirm = vi.fn(() => true)
    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('confirm', confirm)
    render(<App />)
    expect(await screen.findByRole('form', { name: 'Dados de nascimento' })).toBeInTheDocument()
    const deleteButton = screen.getByRole('button', { name: 'Apagar conta' })
    expect(deleteButton).toHaveClass('danger')
    fireEvent.click(deleteButton)
    expect(confirm).toHaveBeenCalledWith('Queres mesmo apagar a conta? Esta ação é irreversível.')
    expect(await screen.findByRole('form', { name: 'Criar conta' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/me',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('mostra o erro do mapa depois de guardar os dados de nascimento', async () => {
    let saved = false
    vi.stubGlobal(
      'fetch',
      route({
        'GET /api/v1/me': () => json(ME),
        'GET /api/v1/me/birth': () => (saved ? json({}) : json({ detail: 'sem dados' }, 404)),
        'PUT /api/v1/me/birth': () => {
          saved = true
          return json({})
        },
        'GET /api/v1/me/chart': () => json({ detail: 'Placidus não está definido' }, 422),
        'GET /api/v1/places?q=Lisb': () =>
          json({
            results: [
              {
                id: 1,
                name: 'Lisbon',
                region: 'Lisbon',
                country_code: 'PT',
                latitude: 38.7,
                longitude: -9.1,
                zone: 'Europe/Lisbon',
              },
            ],
            attribution: 'GeoNames',
          }),
      }),
    )
    render(<App />)
    const form = await screen.findByRole('form', { name: 'Dados de nascimento' })
    fireEvent.change(screen.getByLabelText('Data de nascimento'), { target: { value: '1993-05-20' } })
    fireEvent.change(screen.getByLabelText('Hora exata'), { target: { value: '14:35' } })
    fireEvent.change(screen.getByLabelText('Local de nascimento'), { target: { value: 'Lisb' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Lisbon, Lisbon, Portugal' }))
    fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toHaveTextContent('Placidus')
  })

  it('mostra erro quando o servidor falha', async () => {
    vi.stubGlobal('fetch', route({ 'GET /api/v1/me': () => new Response('', { status: 503 }) }))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Erro 503')
  })
})
