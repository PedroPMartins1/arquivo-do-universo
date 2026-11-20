import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ChartExplorer } from './ChartExplorer'
import type { NatalChart } from './api'

const CHART: NatalChart = {
  bodies: [
    { body: 'sun', longitude: 59, sign: 'taurus', degree_in_sign: 29, house: 3, retrograde: false },
    { body: 'moon', longitude: 119, sign: 'cancer', degree_in_sign: 29, house: 5, retrograde: false },
  ],
  houses: Array.from({ length: 12 }, (_, index) => ({ house: index + 1, longitude: (350 + index * 30) % 360 })),
  angles: { ascendant: 350, midheaven: 260, descendant: 170, imum_coeli: 80 },
  aspects: [{ first: 'sun', second: 'moon', kind: 'sextile', orb: 0, applying: true }],
  calculation: { warnings: [] },
}
const panel = () => within(screen.getByRole('region', { name: 'Elemento selecionado' }))
beforeEach(() => {
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callback(0); return 1 })
  Element.prototype.scrollIntoView = vi.fn()
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('Exploração do mapa natal', () => {
  it('seleciona um planeta na roda com toque e teclado e mostra os dados calculados', () => {
    render(<ChartExplorer chart={CHART} />)
    expect(screen.queryByRole('region', { name: 'Elemento selecionado' })).not.toBeInTheDocument()
    const moon = screen.getByRole('button', { name: 'Explorar Lua' })
    fireEvent.click(moon)
    expect(panel().getByRole('heading', { name: 'Lua em Caranguejo' })).toBeInTheDocument()
    expect(panel().getByText('29°00′ de Caranguejo · Casa 5')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Visão geral' }))
    fireEvent.keyDown(screen.getByRole('button', { name: 'Explorar Sol' }), { key: 'Enter' })
    expect(panel().getByRole('heading', { name: 'Sol em Touro' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Visão geral' }))
    fireEvent.keyDown(screen.getByRole('button', { name: 'Explorar Lua' }), { key: ' ' })
    expect(panel().getByRole('heading', { name: 'Lua em Caranguejo' })).toBeInTheDocument()
  })

  it('segue ligações entre planeta, signo e casa sem inferir dados em falta', () => {
    render(<ChartExplorer chart={CHART} />)
    fireEvent.click(screen.getByRole('button', { name: 'Compreender Sol em Touro' }))
    fireEvent.click(panel().getByRole('button', { name: 'Signo Touro' }))
    expect(panel().getByRole('heading', { name: 'Touro' })).toBeInTheDocument()
    expect(panel().getByRole('button', { name: 'Sol · Casa 3' })).toBeInTheDocument()
    fireEvent.click(panel().getByRole('button', { name: 'Sol · Casa 3' }))
    fireEvent.click(panel().getByRole('button', { name: /Casa 3 · Comunicação/ }))
    expect(panel().getByRole('heading', { name: 'Casa 3' })).toBeInTheDocument()
    expect(panel().getByText('Início da casa: 20°00′ de Touro')).toBeInTheDocument()
    expect(panel().getByRole('button', { name: 'Sol em Touro' })).toBeInTheDocument()
  })

  it('abre os dois elementos de um aspeto e destaca a relação calculada', () => {
    render(<ChartExplorer chart={CHART} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explorar elementos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Aspetos' }))
    fireEvent.click(screen.getByRole('button', { name: /Sol · Lua/ }))
    expect(panel().getByRole('heading', { name: 'Sol em sextil com Lua' })).toBeInTheDocument()
    expect(panel().getByText('Ângulo de referência: 60° · Orbe: 0°00′')).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Mapa natal interativo' })).not.toBeInTheDocument()
    fireEvent.click(panel().getByRole('button', { name: /Lua · Emoções e segurança/ }))
    expect(panel().getByRole('heading', { name: 'Lua em Caranguejo' })).toBeInTheDocument()
  })

  it('explica os casos de casa e signo vazios e permite consultar os ângulos', () => {
    render(<ChartExplorer chart={CHART} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explorar a casa 2' }))
    expect(panel().getByText(/Uma casa vazia não significa/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Visão geral' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorar o signo Peixes' }))
    expect(panel().getByText(/Não há planetas ou pontos calculados neste signo/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Visão geral' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorar Ascendente' }))
    expect(panel().getByRole('heading', { name: 'Ascendente em Peixes' })).toBeInTheDocument()
    expect(panel().getByText('20°00′ de Peixes')).toBeInTheDocument()
  })

  it('mantém as seleções disponíveis quando não existem aspetos', () => {
    render(<ChartExplorer chart={{ ...CHART, aspects: [] }} />)
    fireEvent.click(screen.getByRole('button', { name: 'Explorar elementos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Aspetos' }))
    expect(screen.getByText(/Não há aspetos neste resultado/)).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Elemento selecionado' })).not.toBeInTheDocument()
  })
  it('organiza o percurso e permite voltar ao elemento de origem', () => {
    render(<ChartExplorer chart={CHART} />)
    fireEvent.click(screen.getByRole('button', { name: 'Compreender Sol em Touro' }))
    expect(panel().getByRole('heading', { name: 'Como se expressa · Touro' })).toBeInTheDocument()
    expect(panel().getByRole('heading', { name: 'Em que área · Casa 3' })).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Tipo de elemento' })).not.toBeInTheDocument()
    expect(panel().getByRole('button', { name: 'Sol em sextil com Lua' })).not.toBeVisible()
    fireEvent.click(panel().getByRole('button', { name: 'Signo Touro' }))
    fireEvent.click(screen.getByRole('button', { name: 'Voltar ao elemento anterior' }))
    expect(panel().getByRole('heading', { name: 'Sol em Touro' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Voltar à visão geral' }))
    expect(screen.getByRole('group', { name: 'Começar pelo essencial' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Elemento selecionado' })).not.toBeInTheDocument()
  })

})
