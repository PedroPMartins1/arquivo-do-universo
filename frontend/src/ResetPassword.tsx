import { useState, type FormEvent } from 'react'
import { resetPassword } from './api'

export function ResetPasswordForm({
  token,
  onClose,
}: {
  token: string
  onClose: (changed: boolean) => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password'))
    if (password !== String(form.get('confirmation'))) {
      setError('As palavras-passe têm de ser iguais.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await resetPassword(token, password)
      onClose(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" aria-label="Nova palavra-passe" onSubmit={submit}>
      <h2>Nova palavra-passe</h2>
      <label>
        Escolhe uma palavra-passe
        <input
          name="password"
          type="password"
          minLength={10}
          maxLength={200}
          required
          autoComplete="new-password"
        />
      </label>
      <p className="hint">Usa pelo menos 10 caracteres.</p>
      <label>
        Repete a palavra-passe
        <input
          name="confirmation"
          type="password"
          minLength={10}
          maxLength={200}
          required
          autoComplete="new-password"
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={busy}>
        {busy ? 'A guardar…' : 'Guardar nova palavra-passe'}
      </button>
      <button type="button" className="link" disabled={busy} onClick={() => onClose(false)}>
        Voltar ao início
      </button>
    </form>
  )
}
