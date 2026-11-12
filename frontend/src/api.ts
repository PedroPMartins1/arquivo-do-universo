export interface Health {
  status: string
  version: string
}

export async function fetchHealth(): Promise<Health> {
  const response = await fetch('/api/v1/health')
  if (!response.ok) {
    throw new Error(`Erro ${response.status}`)
  }
  return (await response.json()) as Health
}
