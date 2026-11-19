export type ChartSelection =
  | { kind: 'body'; id: string }
  | { kind: 'sign'; index: number }
  | { kind: 'house'; number: number }
  | { kind: 'aspect'; index: number }
  | { kind: 'angle'; id: 'ascendant' | 'midheaven' }

export const signIndex = (longitude: number) => Math.floor(((longitude % 360) + 360) % 360 / 30)

export function sameSelection(first: ChartSelection | null, second: ChartSelection) {
  if (!first || first.kind !== second.kind) return false
  switch (second.kind) {
    case 'body': return first.kind === 'body' && first.id === second.id
    case 'sign': return first.kind === 'sign' && first.index === second.index
    case 'house': return first.kind === 'house' && first.number === second.number
    case 'aspect': return first.kind === 'aspect' && first.index === second.index
    case 'angle': return first.kind === 'angle' && first.id === second.id
  }
}
