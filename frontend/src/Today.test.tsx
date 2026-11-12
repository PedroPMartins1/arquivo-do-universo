import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { type DailySky, type Me } from './api'
import { Today } from './Today'

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

const todayCalls = (fetchMock: ReturnType<typeof vi.fn>) =>
  fetchMock.mock.calls.filter(([url]) => String(url).includes('/me/today')).length

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Today', () => {
  it('mostra as revelações do dia', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(json(SKY))))
    render(<Today me={ME} onMoved={() => undefined} />)
    expect(await screen.findByRole('heading', { name: 'Revelações do dia' })).toBeInTheDocument()
    expect(screen.getByText(/Saturno em quadratura com Júpiter natal/)).toBeInTheDocument()
  })

  it('volta a pedir o céu quando a residência muda, mesmo dentro do mesmo fuso', async () => {
    const fetchMock = vi.fn(() => Promise.resolve(json(SKY)))
    vi.stubGlobal('fetch', fetchMock)
    const { rerender } = render(<Today me={ME} onMoved={() => undefined} />)
    await screen.findByRole('heading', { name: 'Revelações do dia' })
    expect(todayCalls(fetchMock)).toBe(1)
    rerender(<Today me={{ ...ME, residence_name: 'Sintra' }} onMoved={() => undefined} />)
    await waitFor(() => expect(todayCalls(fetchMock)).toBe(2))
  })

  it('limpa o erro quando uma leitura posterior tem sucesso', async () => {
    let calls = 0
    const fetchMock = vi.fn(() => {
      calls += 1
      return Promise.resolve(calls === 1 ? json({ detail: 'falhou' }, 500) : json(SKY))
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
})
