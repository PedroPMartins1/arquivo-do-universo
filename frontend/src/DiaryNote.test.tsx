import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DiaryNote } from './DiaryNote'

const json = (body: unknown) => new Response(JSON.stringify(body))
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('Acesso direto ao Diário', () => {
  it('recupera a nota existente antes de permitir editar e grava pelo mesmo contrato', async () => {
    const saved = { day: '2026-11-19', slot: null, body: 'Uma nota que já existia.', created_at: '2026-11-19T12:00:00Z', updated_at: '2026-11-19T12:00:00Z', provenance: 'user_reported' }
    const onSaved = vi.fn()
    const fetchMock = vi.fn((_url: string, init?: RequestInit) => Promise.resolve(json(init?.method === 'PUT' ? { ...saved, body: JSON.parse(String(init.body)).body } : [saved])))
    vi.stubGlobal('fetch', fetchMock)
    render(<DiaryNote zone="Europe/Lisbon" onSaved={onSaved} />)
    expect(await screen.findByText(saved.body)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nota do dia'), { target: { value: 'A mesma nota, com mais uma ideia.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(screen.getByText('A mesma nota, com mais uma ideia.', { selector: 'p' })).toBeInTheDocument())
    await waitFor(() => expect(onSaved).toHaveBeenCalledOnce())
    expect(fetchMock).toHaveBeenLastCalledWith(expect.stringMatching(/\/me\/reflections\/\d{4}-\d{2}-\d{2}\/note$/), expect.objectContaining({ method: 'PUT' }))
  })

  it('não apresenta um editor vazio quando não consegue carregar a nota e permite repetir', async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new Error('indisponível')).mockResolvedValueOnce(json([]))
    vi.stubGlobal('fetch', fetchMock)
    render(<DiaryNote zone="Europe/Lisbon" onSaved={() => undefined} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível abrir a tua nota')
    expect(screen.queryByLabelText('Nota do dia')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByLabelText('Nota do dia')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeDisabled()
  })
})
