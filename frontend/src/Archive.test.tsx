import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ArchiveDayDetail, ArchivePage } from './api'
import { Archive } from './Archive'

const json = (body: unknown) => new Response(JSON.stringify(body))
const firstPage: ArchivePage = {
  days: [
    {
      date: '2026-11-16',
      theme: 'Ritmo do dia',
      revelation_count: 2,
      reflection_count: 1,
      has_note: true,
    },
    {
      date: '2026-11-15',
      theme: 'Outro tema',
      revelation_count: 1,
      reflection_count: 2,
      has_note: false,
    },
  ],
  next_before: '2026-11-15',
}
const detail: ArchiveDayDetail = {
  date: '2026-11-16',
  theme: 'Ritmo do dia',
  revelations: [
    { unlocks_at: '2026-11-16T13:00:00Z', reading: null, origin: null },
    {
      unlocks_at: '2026-11-16T11:00:00Z',
      reading: {
        title: 'Um convite à pausa',
        text: 'Este trânsito convida-te a observar os teus limites.',
        question: 'Que espaço podes criar?',
      },
      origin: null,
    },
  ],
  reflections: [],
  model: 'fake-claude',
  prompt_version: 'test',
  generated_at: '2026-11-16T00:00:00Z',
  epistemic_class: 'interpretation',
  note: 'Interpretação simbólica.',
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('Arquivo', () => {
  it('agrupa por mês, abre um dia e regressa à lista', async () => {
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(url.includes('/archive/2026-11-16') ? json(detail) : json(firstPage)),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<Archive zone="Europe/Lisbon" />)
    expect(await screen.findByRole('heading', { name: 'novembro de 2026' })).toBeInTheDocument()
    expect(screen.getByText('1 reflexão')).toBeInTheDocument()
    expect(screen.getByText('2 reflexões')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Ritmo do dia/ }))
    expect(await screen.findByRole('heading', { name: 'segunda-feira, 16 de novembro de 2026' })).toBeInTheDocument()
    expect(screen.getByText('Um convite à pausa')).toBeInTheDocument()
    expect(screen.getByText('Abre às 13:00')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '← Voltar ao Arquivo' }))
    expect(await screen.findByRole('heading', { name: 'novembro de 2026' })).toBeInTheDocument()
  })

  it('carrega a página seguinte usando next_before', async () => {
    const older: ArchivePage = {
      days: [
        {
          date: '2026-10-31',
          theme: null,
          revelation_count: 0,
          reflection_count: 1,
          has_note: true,
        },
      ],
      next_before: null,
    }
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(url.includes('?before=2026-11-15') ? json(older) : json(firstPage)),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<Archive zone="Europe/Lisbon" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Ver mais' }))
    expect(await screen.findByRole('heading', { name: 'outubro de 2026' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/me/archive?before=2026-11-15',
      expect.anything(),
    )
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Ver mais' })).toBeNull())
  })

  it('mostra o estado vazio', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(json({ days: [], next_before: null }))),
    )
    render(<Archive zone="Europe/Lisbon" />)
    expect(
      await screen.findByText(
        'O teu Arquivo começa hoje: as leituras e reflexões de cada dia vão ficando guardadas aqui.',
      ),
    ).toBeInTheDocument()
  })
})
