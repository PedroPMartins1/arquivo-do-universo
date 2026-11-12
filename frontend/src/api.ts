export interface Health {
  status: string
  version: string
}

export interface Me {
  id: string
  email: string
  display_name: string
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
  sign: string
  degree_in_sign: number
  house: number
  retrograde: boolean
}

export interface NatalChart {
  bodies: BodyPosition[]
  angles: { ascendant: number; midheaven: number }
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
