import { useEffect, useState } from 'react'
import { fetchHealth, type Health } from './api'

type State =
  | { kind: 'loading' }
  | { kind: 'ok'; health: Health }
  | { kind: 'error'; message: string }

function App() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    fetchHealth()
      .then((health) => setState({ kind: 'ok', health }))
      .catch((error: unknown) =>
        setState({ kind: 'error', message: error instanceof Error ? error.message : String(error) }),
      )
  }, [])

  return (
    <main>
      <h1>Arquivo do Universo</h1>
      <p className="subtitle">Inteligência Pessoal</p>
      <section aria-label="Estado do sistema">
        {state.kind === 'loading' && <p>A verificar o servidor…</p>}
        {state.kind === 'ok' && (
          <p>
            Servidor: <strong>{state.health.status}</strong> (versão {state.health.version})
          </p>
        )}
        {state.kind === 'error' && <p role="alert">Servidor indisponível: {state.message}</p>}
      </section>
    </main>
  )
}

export default App
