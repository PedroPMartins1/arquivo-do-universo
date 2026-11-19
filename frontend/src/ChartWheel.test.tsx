import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { NatalChart } from './api'
import { ChartWheel } from './ChartWheel'

const CHART: NatalChart = {
  bodies: [
    {
      body: 'sun',
      longitude: 0,
      sign: 'aries',
      degree_in_sign: 0,
      house: 1,
      retrograde: false,
    },
    {
      body: 'moon',
      longitude: 90,
      sign: 'cancer',
      degree_in_sign: 0,
      house: 4,
      retrograde: true,
    },
  ],
  houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, longitude: i * 30 })),
  angles: { ascendant: 0, midheaven: 90, descendant: 180, imum_coeli: 270 },
  aspects: [{ first: 'sun', second: 'moon', kind: 'trine', orb: 0, applying: true }],
  calculation: { warnings: [] },
}

describe('ChartWheel', () => {
  it('desenha a roda com signos, casas, planetas e ASC/MC', () => {
    render(<ChartWheel chart={CHART} />)
    const wheel = screen.getByRole('img', { name: 'Roda do mapa natal' })
    expect(wheel).toBeInTheDocument()
    expect(screen.getByText('♈')).toBeInTheDocument()
    expect(screen.getByText('Peixes')).toBeInTheDocument()
    expect(screen.getByText('ASC')).toBeInTheDocument()
    expect(screen.getByText('MC')).toBeInTheDocument()
    expect(document.querySelectorAll('.wheel-cusp')).toHaveLength(12)
    expect(document.querySelectorAll('.wheel-aspect')).toHaveLength(1)

    fireEvent.click(screen.getByRole('button', { name: 'Ampliar mapa' }))
    expect(screen.getByRole('region', { name: 'Mapa ampliado' })).toHaveAttribute('tabindex', '0')
    expect(screen.getByRole('button', { name: 'Reduzir mapa' })).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Reduzir mapa' }))
    expect(screen.queryByRole('region', { name: 'Mapa ampliado' })).not.toBeInTheDocument()
    expect(wheel).toBeInTheDocument()
  })
})
