import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import type { NatalChart } from './api'
import { ASPECTS, BODIES, SIGNS } from './labels'
import { planetLabelRadii } from './chartLayout'
import { sameSelection, signIndex, type ChartSelection } from './chartSelection'

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

interface WheelProps {
  chart: NatalChart
  selection?: ChartSelection | null
  onSelect?: (selection: ChartSelection) => void
}

export function ChartWheel({ chart, selection, onSelect }: WheelProps) {
  const [enlarged, setEnlarged] = useState(false)
  const viewport = useRef<HTMLDivElement>(null)
  const viewportId = useId()

  useEffect(() => {
    if (enlarged && viewport.current) {
      const panel = viewport.current
      panel.scrollLeft = (panel.scrollWidth - panel.clientWidth) / 2
      panel.scrollTop = (panel.scrollHeight - panel.clientHeight) / 2
    }
  }, [enlarged])

  return (
    <div className="chart-viewer">
      <button
        type="button"
        className="chart-zoom"
        aria-controls={viewportId}
        aria-expanded={enlarged}
        onClick={() => setEnlarged(!enlarged)}
      >
        {enlarged ? 'Reduzir mapa' : 'Ampliar mapa'}
      </button>
      <div
        id={viewportId}
        ref={viewport}
        className={enlarged ? 'chart-viewport enlarged' : 'chart-viewport'}
        role={enlarged ? 'region' : undefined}
        aria-label={enlarged ? 'Mapa ampliado' : undefined}
        tabIndex={enlarged ? 0 : undefined}
      >
        <WheelGraphic chart={chart} selection={selection} onSelect={onSelect} />
      </div>
    </div>
  )
}

function WheelGraphic({ chart, selection = null, onSelect }: WheelProps) {
  const activate = (item: ChartSelection, label: string) => onSelect ? {
    role: 'button' as const,
    tabIndex: 0,
    'aria-label': label,
    'aria-pressed': sameSelection(selection, item),
    onClick: () => onSelect(item),
    onKeyDown: (event: KeyboardEvent<SVGElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        onSelect(item)
      }
    },
  } : {}
  const selectedBody = (id: string) => {
    if (selection?.kind === 'body') return selection.id === id
    if (selection?.kind === 'aspect') {
      const aspect = chart.aspects[selection.index]
      return aspect?.first === id || aspect?.second === id
    }
    const body = chart.bodies.find((item) => item.body === id)
    return body && (selection?.kind === 'sign' && signIndex(body.longitude) === selection.index || selection?.kind === 'house' && body.house === selection.number)
  }

  const bodyPoint = new Map(chart.bodies.map((b) => [b.body, polar(b.longitude, R_PLANETS)]))
  const labelRadii = planetLabelRadii(chart.bodies, R_PLANETS)
  return (
    <svg
      className="chart-wheel"
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role={onSelect ? 'group' : 'img'}
      aria-label={onSelect ? 'Mapa natal interativo' : 'Roda do mapa natal'}
    >
      <circle cx={C} cy={C} r={R_SIGN_OUT + 6} className="wheel-outer" />
      <path d={ringPath(R_SIGN_IN, R_SIGN_OUT)} className="wheel-sign-band" fillRule="evenodd" />
      {SIGNS.map((sign, i) => {
        const [gx, gy] = polar(i * 30 + 15, (R_SIGN_IN + R_SIGN_OUT) / 2)
        return (
          <g key={sign} className={`wheel-target${sameSelection(selection, { kind: 'sign', index: i }) ? ' is-selected' : ''}`} {...activate({ kind: 'sign', index: i }, `Explorar o signo ${sign}`)}>
            <circle cx={gx} cy={gy} r="22" className="wheel-hit" />
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
          <g key={h.house} className={`wheel-target${sameSelection(selection, { kind: 'house', number: h.house }) ? ' is-selected' : ''}`} {...activate({ kind: 'house', number: h.house }, `Explorar a casa ${h.house}`)}>
            <circle cx={lx} cy={ly} r="16" className="wheel-hit" />
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
          <g key={`${a.first}-${a.second}-${i}`} className={`wheel-target${sameSelection(selection, { kind: 'aspect', index: i }) ? ' is-selected' : ''}${selection?.kind === 'body' && (a.first === selection.id || a.second === selection.id) ? ' is-related' : ''}`} {...activate({ kind: 'aspect', index: i }, `Explorar ${BODIES[a.first] ?? a.first} em ${ASPECTS[a.kind] ?? a.kind} com ${BODIES[a.second] ?? a.second}`)}>
          <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} className="wheel-aspect-hit" />
          <line
            x1={p1[0]}
            y1={p1[1]}
            x2={p2[0]}
            y2={p2[1]}
            stroke={ASPECT_COLORS[a.kind] ?? '#888'}
            strokeOpacity={Math.max(0.25, 0.8 - a.orb / 10)}
            className="wheel-aspect"
          />
          </g>
        )
      })}
      <circle cx={C} cy={C} r={R_PLANETS + 14} className="wheel-planet-ring" />
      {chart.bodies.map((b) => {
        const [anchorX, anchorY] = bodyPoint.get(b.body) ?? polar(b.longitude, R_PLANETS)
        const [x, y] = polar(b.longitude, labelRadii.get(b.body) ?? R_PLANETS)
        return (
          <g key={b.body} className={`wheel-target${selectedBody(b.body) ? ' is-selected' : ''}`} {...activate({ kind: 'body', id: b.body }, `Explorar ${BODIES[b.body] ?? b.body}`)}>
            {(x !== anchorX || y !== anchorY) && <line x1={anchorX} y1={anchorY} x2={x} y2={y} className="wheel-label-guide" />}
            <circle cx={anchorX} cy={anchorY} r="2" className="wheel-position-dot" />
            <circle cx={x} cy={y} r="18" className="wheel-hit" />
            <text
              x={x}
              y={y}
              className={`wheel-planet${b.retrograde ? ' retrograde' : ''}`}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {BODY_GLYPHS[b.body] ?? b.body}
            </text>
            <title>{`${BODIES[b.body] ?? b.body}${b.retrograde ? ' (retrógrado)' : ''}`}</title>
          </g>
        )
      })}
      <text
        x={polar(chart.angles.ascendant, R_PLANETS + 7)[0]}
        y={polar(chart.angles.ascendant, R_PLANETS + 7)[1]}
        {...activate({ kind: 'angle', id: 'ascendant' }, 'Explorar Ascendente')}
        className="wheel-angle wheel-target"
        textAnchor="middle"
        dominantBaseline="central"
      >
        ASC
      </text>
      <text
        x={polar(chart.angles.midheaven, R_PLANETS + 7)[0]}
        y={polar(chart.angles.midheaven, R_PLANETS + 7)[1]}
        {...activate({ kind: 'angle', id: 'midheaven' }, 'Explorar Meio do Céu')}
        className="wheel-angle wheel-target"
        textAnchor="middle"
        dominantBaseline="central"
      >
        MC
      </text>
    </svg>
  )
}
