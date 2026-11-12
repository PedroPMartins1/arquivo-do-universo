import { type FormEvent, useCallback, useEffect, useState } from 'react'
import {
  ApiError,
  type BirthData,
  fetchBirth,
  fetchChart,
  fetchMe,
  login,
  logout,
  type Me,
  type NatalChart,
  type Place,
  register,
  saveBirth,
} from './api'
import { BODIES, degrees, describePlace, signName, signOfLongitude } from './labels'
import { PlaceSearch } from './PlaceSearch'
import { ChartWheel } from './ChartWheel'
import { Today } from './Today'

type State =
  | { kind: 'loading' }
  | { kind: 'anonymous' }
  | { kind: 'needs-birth'; me: Me; problem?: string }
  | { kind: 'ready'; me: Me; chart: NatalChart }
  | { kind: 'error'; message: string }

const messageOf = (error: unknown) => (error instanceof Error ? error.message : String(error))

function AuthForm({ onDone }: { onDone: () => unknown }) {
  const [mode, setMode] = useState<'login' | 'register'>('register')
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email'))
    const password = String(form.get('password'))
    try {
      if (mode === 'register') await register(email, password, String(form.get('name')))
      else await login(email, password)
      onDone()
    } catch (err) {
      setError(messageOf(err))
    }
  }

  return (
    <form className="card" onSubmit={submit} aria-label={mode === 'register' ? 'Criar conta' : 'Entrar'}>
      <h2>{mode === 'register' ? 'Criar conta' : 'Entrar'}</h2>
      {mode === 'register' && (
        <label>
          Nome
          <input name="name" required maxLength={200} autoComplete="given-name" />
        </label>
      )}
      <label>
        Email
        <input name="email" type="email" required autoComplete="email" />
      </label>
      <label>
        Palavra-passe
        <input
          name="password"
          type="password"
          required
          minLength={mode === 'register' ? 10 : undefined}
          autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit">{mode === 'register' ? 'Criar conta' : 'Entrar'}</button>
      <button
        type="button"
        className="link"
        onClick={() => {
          setError(null)
          setMode(mode === 'register' ? 'login' : 'register')
        }}
      >
        {mode === 'register' ? 'Já tenho conta' : 'Criar uma conta nova'}
      </button>
    </form>
  )
}

function BirthForm({ onDone, problem }: { onDone: () => unknown; problem?: string }) {
  const [error, setError] = useState<string | null>(problem ?? null)
  const [ambiguous, setAmbiguous] = useState(false)
  const [place, setPlace] = useState<Place | null>(null)
  const [manual, setManual] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const occurrence = form.get('occurrence')
    if (!manual && !place) {
      setError('Escolhe o local de nascimento na lista.')
      return
    }
    const where = manual
      ? {
          place_name: String(form.get('place_name')),
          latitude: Number(form.get('latitude')),
          longitude: Number(form.get('longitude')),
          zone: null,
        }
      : {
          place_name: describePlace(place as Place).slice(0, 200),
          latitude: (place as Place).latitude,
          longitude: (place as Place).longitude,
          zone: (place as Place).zone,
        }
    const data: BirthData = {
      birth_date: String(form.get('birth_date')),
      birth_time: String(form.get('birth_time')),
      ...where,
      occurrence: occurrence === null ? null : (Number(occurrence) as 0 | 1),
    }
    try {
      await saveBirth(data)
      onDone()
    } catch (err) {
      setError(messageOf(err))
      if (err instanceof ApiError && err.message.includes('duas vezes')) setAmbiguous(true)
    }
  }

  return (
    <form className="card" onSubmit={submit} aria-label="Dados de nascimento">
      <h2>O momento em que chegaste</h2>
      <p className="hint">
        O teu mapa depende do minuto exato e do local onde nasceste. Confirma a hora na certidão de
        nascimento.
      </p>
      <label>
        Data de nascimento
        <input name="birth_date" type="date" required />
      </label>
      <label>
        Hora exata
        <input name="birth_time" type="time" step={60} required />
      </label>
      {manual ? (
        <>
          <label>
            Local de nascimento
            <input name="place_name" required maxLength={200} />
          </label>
          <div className="row">
            <label>
              Latitude
              <input name="latitude" type="number" step="any" min={-90} max={90} required />
            </label>
            <label>
              Longitude
              <input name="longitude" type="number" step="any" min={-180} max={180} required />
            </label>
          </div>
        </>
      ) : (
        <PlaceSearch onSelect={setPlace} />
      )}
      <button type="button" className="link" onClick={() => {
          setPlace(null)
          setManual(!manual)
        }}>
        {manual ? 'Procurar o local pelo nome' : 'Não encontro o meu local: indicar coordenadas'}
      </button>
      {ambiguous && (
        <fieldset>
          <legend>Nesse dia o relógio atrasou e esta hora aconteceu duas vezes</legend>
          <label className="inline">
            <input type="radio" name="occurrence" value="0" required /> Primeira vez (hora de verão)
          </label>
          <label className="inline">
            <input type="radio" name="occurrence" value="1" /> Segunda vez (hora de inverno)
          </label>
        </fieldset>
      )}
      {error && <p role="alert">{error}</p>}
      <button type="submit">Revelar o meu mapa</button>
    </form>
  )
}

function ChartSummary({ chart }: { chart: NatalChart }) {
  const sun = chart.bodies.find((b) => b.body === 'sun')
  const moon = chart.bodies.find((b) => b.body === 'moon')
  return (
    <section className="card" aria-label="O teu mapa natal">
      <h2>O teu mapa natal</h2>
      <ChartWheel chart={chart} />
      <dl className="big-three">
        <div>
          <dt>Sol</dt>
          <dd>{sun && signName(sun.sign)}</dd>
        </div>
        <div>
          <dt>Lua</dt>
          <dd>{moon && signName(moon.sign)}</dd>
        </div>
        <div>
          <dt>Ascendente</dt>
          <dd>{signOfLongitude(chart.angles.ascendant)}</dd>
        </div>
      </dl>
      <table>
        <thead>
          <tr>
            <th>Corpo</th>
            <th>Signo</th>
            <th>Grau</th>
            <th>Casa</th>
          </tr>
        </thead>
        <tbody>
          {chart.bodies.map((b) => (
            <tr key={b.body}>
              <td>
                {BODIES[b.body] ?? b.body}
                {b.retrograde && <abbr title="retrógrado"> ℞</abbr>}
              </td>
              <td>{signName(b.sign)}</td>
              <td>{degrees(b.degree_in_sign)}</td>
              <td>{b.house}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {chart.calculation.warnings.map((w) => (
        <p key={w} className="hint">
          {w}
        </p>
      ))}
    </section>
  )
}

async function loadState(): Promise<State> {
  try {
    const me = await fetchMe()
    try {
      await fetchBirth()
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return { kind: 'needs-birth', me }
      throw err
    }
    try {
      return { kind: 'ready', me, chart: await fetchChart() }
    } catch (err) {
      if (err instanceof ApiError && err.status === 422)
        return { kind: 'needs-birth', me, problem: err.message }
      throw err
    }
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return { kind: 'anonymous' }
    return { kind: 'error', message: messageOf(err) }
  }
}

function App() {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const refresh = useCallback(() => loadState().then(setState), [])

  useEffect(() => {
    void loadState().then(setState)
  }, [])
  const signedIn = state.kind === 'needs-birth' || state.kind === 'ready'

  return (
    <main>
      <header>
        <h1>Arquivo do Universo</h1>
        {signedIn && (
          <button type="button" className="link" onClick={() => void logout().then(refresh)}>
            Sair
          </button>
        )}
      </header>
      {signedIn && <p className="subtitle">Olá, {state.me.display_name}.</p>}
      {state.kind === 'loading' && <p>A consultar as estrelas…</p>}
      {state.kind === 'error' && <p role="alert">Servidor indisponível: {state.message}</p>}
      {state.kind === 'anonymous' && <AuthForm onDone={refresh} />}
      {state.kind === 'needs-birth' && <BirthForm onDone={refresh} problem={state.problem} />}
      {state.kind === 'ready' && (
        <>
          <Today me={state.me} onMoved={refresh} />
          <ChartSummary chart={state.chart} />
        </>
      )}
    </main>
  )
}

export default App
