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
