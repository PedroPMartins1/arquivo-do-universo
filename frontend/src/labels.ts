import type { Place } from './api'

export const SIGNS = [
  'Carneiro',
  'Touro',
  'Gémeos',
  'Caranguejo',
  'Leão',
  'Virgem',
  'Balança',
  'Escorpião',
  'Sagitário',
  'Capricórnio',
  'Aquário',
  'Peixes',
] as const

const SIGN_KEYS = [
  'aries',
  'taurus',
  'gemini',
  'cancer',
  'leo',
  'virgo',
  'libra',
  'scorpio',
  'sagittarius',
  'capricorn',
  'aquarius',
  'pisces',
]

export const BODIES: Record<string, string> = {
  sun: 'Sol',
  moon: 'Lua',
  mercury: 'Mercúrio',
  venus: 'Vénus',
  mars: 'Marte',
  jupiter: 'Júpiter',
  saturn: 'Saturno',
  uranus: 'Úrano',
  neptune: 'Neptuno',
  pluto: 'Plutão',
  north_node: 'Nodo Norte',
  chiron: 'Quíron',
}

export const signName = (key: string) => SIGNS[SIGN_KEYS.indexOf(key)] ?? key
export const signOfLongitude = (longitude: number) => SIGNS[Math.floor((((longitude % 360) + 360) % 360) / 30)]
export const degrees = (value: number) => {
  const whole = Math.floor(value)
  return `${whole}°${String(Math.floor((value - whole) * 60)).padStart(2, '0')}′`
}

const countries = new Intl.DisplayNames(['pt-PT'], { type: 'region' })

export const describePlace = (place: Place) =>
  [place.name, place.region, countries.of(place.country_code)].filter(Boolean).join(', ')

export const POINTS: Record<string, string> = { ...BODIES, ascendant: 'Ascendente', midheaven: 'Meio do Céu' }

export const ASPECTS: Record<string, string> = {
  conjunction: 'conjunção',
  sextile: 'sextil',
  square: 'quadratura',
  trine: 'trígono',
  opposition: 'oposição',
}

const ECLIPSES: Record<string, string> = {
  total: 'total',
  annular: 'anular',
  partial: 'parcial',
  hybrid: 'híbrido',
  penumbral: 'penumbral',
}

export function describeEvent(e: {
  kind: string
  body: string
  sign: string | null
  natal_house: number | null
  eclipse_type: string | null
}) {
  const body = BODIES[e.body] ?? e.body
  const sign = e.sign ? signName(e.sign) : ''
  const house = e.natal_house ? `, na tua casa ${e.natal_house}` : ''
  const eclipse = ECLIPSES[e.eclipse_type ?? ''] ?? ''
  switch (e.kind) {
    case 'sign_ingress':
      return `${body} entra em ${sign}`
    case 'house_ingress':
      return `${body} entra na tua casa ${e.natal_house}`
    case 'station_retrograde':
      return `${body} fica retrógrado em ${sign}${house}`
    case 'station_direct':
      return `${body} retoma o movimento direto em ${sign}${house}`
    case 'new_moon':
      return `Lua Nova em ${sign}${house}`
    case 'full_moon':
      return `Lua Cheia em ${sign}${house}`
    case 'solar_eclipse':
      return `Eclipse solar ${eclipse} em ${sign}${house}`
    case 'lunar_eclipse':
      return `Eclipse lunar ${eclipse} em ${sign}${house}`
    default:
      return e.kind
  }
}

export const describeTransit = (t: { body: string; kind: string; natal_point: string }) =>
  `${BODIES[t.body] ?? t.body} em ${ASPECTS[t.kind] ?? t.kind} com ${POINTS[t.natal_point] ?? t.natal_point} natal`
