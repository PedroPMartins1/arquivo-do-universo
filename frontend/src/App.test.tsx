import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('mostra o estado do servidor', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: 'ok', version: '0.1.0' }), { status: 200 }),
      ),
    )
    render(<App />)
    expect(await screen.findByText('ok')).toBeInTheDocument()
  })

  it('mostra erro quando o servidor falha', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Erro 503')
  })
})
