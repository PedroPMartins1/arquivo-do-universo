import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const ME = { id: '1', email: 'ana@example.org', display_name: 'Ana' }
const CHART = {
  bodies: [
    { body: 'sun', sign: 'taurus', degree_in_sign: 29.5, house: 9, retrograde: false },
    { body: 'moon', sign: 'pisces', degree_in_sign: 3.25, house: 6, retrograde: false },
  ],
  angles: { ascendant: 155.2, midheaven: 60 },
  calculation: { warnings: [] },
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
        'GET /api/v1/me/birth': () => (saved ? json({}) : json({ detail: 'sem dados' }, 404)),
        'PUT /api/v1/me/birth': () => {
          saved = true
          return json({})
        },
        'GET /api/v1/me/chart': () => json(CHART),
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
    expect(await screen.findAllByText('Touro')).toHaveLength(2)
    expect(screen.getAllByText('Peixes')).toHaveLength(2)
    expect(screen.getByText('Virgem')).toBeInTheDocument()
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

  it('mostra erro quando o servidor falha', async () => {
    vi.stubGlobal('fetch', route({ 'GET /api/v1/me': () => new Response('', { status: 503 }) }))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Erro 503')
  })
})
