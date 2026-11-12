import type { NatalChart } from './api'
import { SIGNS } from './labels'

const SIZE = 580
const C = SIZE / 2
const R_SIGN_IN = 232
const R_SIGN_OUT = 268
const R_HOUSES = 190
const R_PLANETS = 132

const SIGN_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

const BODY_GLYPHS: Record<string, string> = {
  sun: '☉',
  moon: '☽',
  mercury: '☿',
  venus: '♀',
  mars: '♂',
  jupiter: '♃',
  saturn: '♄',
  uranus: '♅',
  neptune: '♆',
  pluto: '♇',
  north_node: '☊',
  chiron: '⚷',
}

const ASPECT_COLORS: Record<string, string> = {
  conjunction: '#e9d8a6',
  opposition: '#d97b7b',
  square: '#d98a5a',
  trine: '#7fae8b',
  sextile: '#7fa8b8',
}

/** Posição na roda: longitude eclíptica com 0° de Carneiro à esquerda, signos diretos. */
function polar(longitude: number, radius: number): [number, number] {
  const theta = ((180 - longitude) * Math.PI) / 180
  return [C + radius * Math.cos(theta), C - radius * Math.sin(theta)]
}

function ringPath(inner: number, outer: number): string {
  const parts: string[] = []
  for (const radius of [outer, inner]) {
    for (let i = 0; i <= 36; i += 1) {
      const lambda = i * 10
      const [x, y] = polar(lambda, radius)
      parts.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`)
    }
    parts.push('Z')
  }
  return parts.join(' ')
}

export function ChartWheel({ chart }: { chart: NatalChart }) {
  const bodyPoint = new Map(chart.bodies.map((b) => [b.body, polar(b.longitude, R_PLANETS)]))
  return (
    <svg
      className="chart-wheel"
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role="img"
      aria-label="Roda do mapa natal"
    >
      <circle cx={C} cy={C} r={R_SIGN_OUT + 6} className="wheel-outer" />
      <path d={ringPath(R_SIGN_IN, R_SIGN_OUT)} className="wheel-sign-band" fillRule="evenodd" />
      {SIGNS.map((sign, i) => {
        const [gx, gy] = polar(i * 30 + 15, (R_SIGN_IN + R_SIGN_OUT) / 2)
        return (
          <g key={sign}>
            <text
              x={gx}
              y={gy - 8}
              className="wheel-glyph"
              textAnchor="middle"
              dominantBaseline="central"
            >
              {SIGN_GLYPHS[i]}
            </text>
            <text
              x={gx}
              y={gy + 12}
              className="wheel-sign"
              textAnchor="middle"
              dominantBaseline="central"
            >
              {sign}
            </text>
          </g>
        )
      })}
      {[...Array(36)].map((_, i) => {
        const lambda = i * 10
        const [x1, y1] = polar(lambda, R_SIGN_IN)
        const [x2, y2] = polar(lambda, R_SIGN_IN - (i % 3 === 0 ? 10 : 5))
        return <line key={lambda} x1={x1} y1={y1} x2={x2} y2={y2} className="wheel-tick" />
      })}
      <circle cx={C} cy={C} r={R_HOUSES} className="wheel-house-ring" />
      {chart.houses.map((h) => {
        const [x, y] = polar(h.longitude, R_HOUSES)
        const [lx, ly] = polar(h.longitude, R_HOUSES - 16)
        return (
          <g key={h.house}>
            <line x1={C} y1={C} x2={x} y2={y} className="wheel-cusp" />
            <text x={lx} y={ly} className="wheel-house" textAnchor="middle" dominantBaseline="central">
              {h.house}
            </text>
          </g>
        )
      })}
      {chart.aspects.map((a, i) => {
        const p1 = bodyPoint.get(a.first)
        const p2 = bodyPoint.get(a.second)
        if (!p1 || !p2) return null
        return (
          <line
            key={`${a.first}-${a.second}-${i}`}
            x1={p1[0]}
            y1={p1[1]}
            x2={p2[0]}
            y2={p2[1]}
            stroke={ASPECT_COLORS[a.kind] ?? '#888'}
            strokeOpacity={Math.max(0.25, 0.8 - a.orb / 10)}
            className="wheel-aspect"
          />
        )
      })}
      <circle cx={C} cy={C} r={R_PLANETS + 14} className="wheel-planet-ring" />
      {chart.bodies.map((b) => {
        const [x, y] = bodyPoint.get(b.body) ?? polar(b.longitude, R_PLANETS)
        return (
          <g key={b.body}>
            <text
              x={x}
              y={y}
              className={`wheel-planet${b.retrograde ? ' retrograde' : ''}`}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {BODY_GLYPHS[b.body] ?? b.body}
            </text>
            <title>{`${b.body}${b.retrograde ? ' (retrógrado)' : ''}`}</title>
          </g>
        )
      })}
      <text
        x={polar(chart.angles.ascendant, R_PLANETS + 7)[0]}
        y={polar(chart.angles.ascendant, R_PLANETS + 7)[1]}
        className="wheel-angle"
        textAnchor="middle"
        dominantBaseline="central"
      >
        ASC
      </text>
      <text
        x={polar(chart.angles.midheaven, R_PLANETS + 7)[0]}
        y={polar(chart.angles.midheaven, R_PLANETS + 7)[1]}
        className="wheel-angle"
        textAnchor="middle"
        dominantBaseline="central"
      >
        MC
      </text>
    </svg>
  )
}
