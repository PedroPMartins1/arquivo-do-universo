export interface Health {
  status: string
  version: string
}

export interface Me {
  id: string
  email: string
  display_name: string
  residence_name?: string | null
  residence_zone?: string | null
}

export interface BirthData {
  birth_date: string
  birth_time: string
  place_name: string
  latitude: number
  longitude: number
  zone?: string | null
  occurrence?: 0 | 1 | null
}

export interface BirthProfile extends BirthData {
  zone: string
  birth_utc: string
}

export interface BodyPosition {
  body: string
  longitude: number
  sign: string
  degree_in_sign: number
  house: number
  retrograde: boolean
}

export interface HouseCusp {
  house: number
  longitude: number
}

export interface NatalAspect {
  first: string
  second: string
  kind: string
  orb: number
  applying: boolean
}

export interface NatalChart {
  bodies: BodyPosition[]
  houses: HouseCusp[]
  angles: { ascendant: number; midheaven: number; descendant: number; imum_coeli: number }
  aspects: NatalAspect[]
  calculation: { warnings: string[] }
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    credentials: 'same-origin',
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })
  if (!response.ok) {
    let message = `Erro ${response.status}`
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) message = 'Há campos inválidos ou em falta.'
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(response.status, message)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

const post = <T>(path: string, body?: unknown, method = 'POST') =>
  request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) })

export const fetchHealth = () => request<Health>('/health')
export const fetchMe = () => request<Me>('/me')
export const register = (email: string, password: string, displayName: string) =>
  post<Me>('/auth/register', { email, password, display_name: displayName })
export const login = (email: string, password: string) =>
  post<Me>('/auth/login', { email, password })
export const logout = () => post<void>('/auth/logout')
export const deleteAccount = () => request<void>('/me', { method: 'DELETE' })
export const fetchBirth = () => request<BirthProfile>('/me/birth')
export const saveBirth = (data: BirthData) => post<BirthProfile>('/me/birth', data, 'PUT')
export const fetchChart = () => request<NatalChart>('/me/chart')

export interface Place {
  id: number
  name: string
  region: string | null
  country_code: string
  latitude: number
  longitude: number
  zone: string
}

export const searchPlaces = (q: string) =>
  request<{ results: Place[]; attribution: string }>(`/places?q=${encodeURIComponent(q)}`)

export interface Transit {
  body: string
  natal_point: string
  kind: string
  starts: string | null
  ends: string | null
  exact: string[]
  orb: number | null
  applying: boolean | null
  natal_house: number
  weight: number
}

export interface SkyEvent {
  kind: string
  at: string
  body: string
  sign: string | null
  natal_house: number | null
  eclipse_type: string | null
  other_body: string | null
  aspect: string | null
  contacts: string[]
  weight: number
}

export interface Factor {
  weight: number
  transit: Transit | null
  event: SkyEvent | null
}

export interface Revelation {
  weight: number
  transit: Transit | null
  event: SkyEvent | null
  focus: string | null
  supporting: Factor[]
}

export interface RevelationSlot {
  unlocks_at: string
  revelation: Revelation | null
}

export interface TodaySky {
  date: string
  zone: string
  day_starts: string
  day_ends: string
  now: string
  revelations: RevelationSlot[]
  tomorrow: Revelation | null
  active: Transit[]
  upcoming: Transit[]
  events: SkyEvent[]
  calculation: {
    library: string
    library_version: string
    orbs: Record<string, number>
    aspects: string[]
    note: string
  }
}

export const fetchToday = () => request<TodaySky>('/me/today')
export interface ReadingSection {
  id: string
  title: string
  text: string
}

export interface NatalReading {
  sections: ReadingSection[]
  model: string
  prompt_version: string
  generated_at: string
  epistemic_class: 'interpretation'
  note: string
}

export interface TodayReading {
  date: string
  theme: string | null
  revelations: (RevelationReading | null)[]
  tomorrow: string | null
  model: string
  prompt_version: string
  generated_at: string
  epistemic_class: 'interpretation'
  note: string
}

export interface RevelationReading {
  title: string
  text: string
  question: string
}

export interface Reflection {
  day: string
  slot: number | null
  question: string | null
  body: string
  created_at: string
  updated_at: string
  provenance: 'user_reported'
}

export interface ArchiveDay {
  date: string
  theme: string | null
  revelation_count: number
  reflection_count: number
  has_note: boolean
}

export interface ArchivePage {
  days: ArchiveDay[]
  next_before: string | null
}

export interface ArchiveDayDetail {
  date: string
  theme: string | null
  revelations: {
    unlocks_at: string
    reading: RevelationReading | null
    origin: Revelation | null
  }[]
  reflections: Reflection[]
  model: string | null
  prompt_version: string | null
  generated_at: string | null
  epistemic_class: 'interpretation' | null
  note: string | null
}

export const fetchNatalReading = () => request<NatalReading>('/me/reading/natal')
export const fetchTodayReading = (day?: string) =>
  request<TodayReading>(`/me/reading/today${day ? `?date=${encodeURIComponent(day)}` : ''}`)
export const saveResidence = (place_name: string, zone: string) =>
  post<Me>('/me/residence', { place_name, zone }, 'PUT')

export const fetchReflections = (day: string) =>
  request<Reflection[]>(`/me/reflections/${encodeURIComponent(day)}`)
export const saveRevelationReflection = (day: string, slot: number, body: string) =>
  post<Reflection>(`/me/reflections/${encodeURIComponent(day)}/revelations/${slot}`, { body }, 'PUT')
export const deleteRevelationReflection = (day: string, slot: number) =>
  request<void>(`/me/reflections/${encodeURIComponent(day)}/revelations/${slot}`, {
    method: 'DELETE',
  })
export const saveNote = (day: string, body: string) =>
  post<Reflection>(`/me/reflections/${encodeURIComponent(day)}/note`, { body }, 'PUT')
export const deleteNote = (day: string) =>
  request<void>(`/me/reflections/${encodeURIComponent(day)}/note`, { method: 'DELETE' })
export const fetchArchive = (before?: string) =>
  request<ArchivePage>(`/me/archive${before ? `?before=${encodeURIComponent(before)}` : ''}`)
export const fetchArchiveDay = (day: string) =>
  request<ArchiveDayDetail>(`/me/archive/${encodeURIComponent(day)}`)
