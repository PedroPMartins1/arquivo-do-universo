import { describe, expect, it } from 'vitest'
import { planetLabelRadii } from './chartLayout'

describe('Símbolos próximos na roda', () => {
  it('afasta símbolos em longitudes próximas ou junto à passagem de 360 graus', () => {
    const bodies = [{ body: 'sun', longitude: 359 }, { body: 'mercury', longitude: 1 }, { body: 'venus', longitude: 2 }]
    const before = structuredClone(bodies)
    const radii = planetLabelRadii(bodies, 132)
    expect(new Set(radii.values()).size).toBe(3)
    expect(bodies).toEqual(before)
  })
  it('mantém o raio base de símbolos que já estão separados', () => {
    expect([...planetLabelRadii([{ body: 'sun', longitude: 0 }, { body: 'moon', longitude: 180 }], 132).values()]).toEqual([132, 132])
  })
})
