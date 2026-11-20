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
      role: 'main',
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
  it('pede uma ligação de recuperação sem pedir a palavra-passe antiga', async () => {
    const fetchMock = route({
      'GET /api/v1/me': () => json({ detail: 'sessão' }, 401),
      'POST /api/v1/auth/forgot-password': () =>
        json({ message: 'Confirma a tua caixa de correio.' }, 202),
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Já tenho conta' }))
    fireEvent.click(screen.getByRole('button', { name: 'Esqueci-me da palavra-passe' }))
    expect(screen.queryByLabelText('Palavra-passe')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'ana@example.org' } })
    fireEvent.submit(screen.getByRole('form', { name: 'Recuperar acesso' }))
    expect(await screen.findByText('Confirma a tua caixa de correio.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/forgot-password',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'ana@example.org' }),
      }),
    )
  })

  it('recebe a ligação, retira o token do endereço e permite escolher nova palavra-passe', async () => {
    window.history.replaceState(null, '', '/#recuperar=token-ficticio-de-utilizacao-unica')
    const fetchMock = route({
      'GET /api/v1/me': () => json({ detail: 'sessão' }, 401),
      'POST /api/v1/auth/reset-password': () => new Response(null, { status: 204 }),
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    expect(screen.getByRole('form', { name: 'Nova palavra-passe' })).toBeInTheDocument()
    expect(window.location.hash).toBe('')
    fireEvent.change(screen.getByLabelText('Escolhe uma palavra-passe'), {
      target: { value: 'nova-password-segura' },
    })
    fireEvent.change(screen.getByLabelText('Repete a palavra-passe'), {
      target: { value: 'outra-password' },
    })
    fireEvent.submit(screen.getByRole('form', { name: 'Nova palavra-passe' }))
    expect(screen.getByRole('alert')).toHaveTextContent('As palavras-passe têm de ser iguais.')
    fireEvent.change(screen.getByLabelText('Repete a palavra-passe'), {
      target: { value: 'nova-password-segura' },
    })
    fireEvent.submit(screen.getByRole('form', { name: 'Nova palavra-passe' }))
    expect(await screen.findByRole('form', { name: 'Entrar' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/reset-password',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          token: 'token-ficticio-de-utilizacao-unica',
          password: 'nova-password-segura',
        }),
      }),
    )
  })

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
    fireEvent.change(screen.getByLabelText('Data de nascimento'), {
      target: { value: '1993-05-20' },
    })
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
    expect(
      screen.getByText('Mercúrio retoma o movimento direto em Escorpião, na tua casa 3'),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mapa Natal' }))
    expect(screen.getByRole('group', { name: 'Começar pelo essencial' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Compreender Sol em Touro' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Compreender Lua em Peixes' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Compreender Ascendente em Virgem' })).toBeInTheDocument()
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
    fireEvent.click(await screen.findByRole('button', { name: 'Mapa Natal' }))
    fireEvent.click(screen.getByText('Leitura integrada do teu mapa'))
    expect(await screen.findByRole('heading', { name: 'A tua leitura' })).toBeInTheDocument()
    expect(await screen.findByText('Uma secção mockada.')).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Mapa natal interativo' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Perfil' }))
    expect(screen.getByRole('heading', { name: 'Dados de nascimento' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apagar conta' })).toBeInTheDocument()
  })

  it('dá acesso direto ao mapa e ao diário sem separadores vazios', async () => {
    vi.stubGlobal('fetch', route({
      'GET /api/v1/me': () => json(ME),
      'GET /api/v1/me/birth': () => json(BIRTH),
      'GET /api/v1/me/chart': () => json(CHART),
      'GET /api/v1/me/today': () => json(SKY),
      'GET /api/v1/me/reading/today': () => json({ theme: null, revelations: [], tomorrow: null }),
      'GET /api/v1/me/archive': () => json({ days: [], next_before: null }),
    }))
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /^Diário$/ }))
    expect(await screen.findByRole('heading', { name: 'Como estás a viver este dia?' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Diário$/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.queryByRole('button', { name: 'Explorar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Jornada' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mapa Natal' })).toBeInTheDocument()
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
    fireEvent.change(screen.getByLabelText('Data de nascimento'), {
      target: { value: '1993-05-20' },
    })
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
