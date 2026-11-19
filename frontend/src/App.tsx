import { type FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import {
  ApiError,
  type BirthData,
  type BirthProfile,
  deleteAccount,
  fetchBirth,
  fetchChart,
  fetchMe,
  fetchNatalReading,
  login,
  logout,
  type Me,
  type NatalChart,
  type NatalReading,
  type Place,
  register,
  requestPasswordRecovery,
  saveBirth,
} from './api'
import { BODIES, degrees, describePlace, signName, signOfLongitude } from './labels'
import { PlaceSearch } from './PlaceSearch'
import { ChartWheel } from './ChartWheel'
import { Archive } from './Archive'
import { Today } from './Today'
import { ResetPasswordForm } from './ResetPassword'

type State =
  | { kind: 'loading' }
  | { kind: 'anonymous' }
  | { kind: 'needs-birth'; me: Me; problem?: string }
  | { kind: 'ready'; me: Me; chart: NatalChart; birth: BirthProfile }
  | { kind: 'error'; message: string }

type Tab = 'today' | 'explore' | 'journey' | 'archive' | 'profile'

const TABS: { id: Tab; label: string }[] = [
  { id: 'today', label: 'Hoje' },
  { id: 'explore', label: 'Explorar' },
  { id: 'journey', label: 'Jornada' },
  { id: 'archive', label: 'Arquivo' },
  { id: 'profile', label: 'Perfil' },
]

const messageOf = (error: unknown) => (error instanceof Error ? error.message : String(error))

function AuthForm({
  onDone,
  initialMode = 'register',
}: {
  onDone: () => unknown
  initialMode?: 'login' | 'register'
}) {
  const [mode, setMode] = useState<'login' | 'register' | 'recover'>(initialMode)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const title =
    mode === 'register' ? 'Criar conta' : mode === 'recover' ? 'Recuperar acesso' : 'Entrar'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email'))
    const password = String(form.get('password'))
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      if (mode === 'recover') {
        const result = await requestPasswordRecovery(email)
        setNotice(result.message)
        return
      }
      if (mode === 'register') await register(email, password, String(form.get('name')))
      else await login(email, password)
      onDone()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={submit} aria-label={title}>
      <h2>{title}</h2>
      {mode === 'register' && (
        <label>
          Nome
          <input name="name" required maxLength={200} autoComplete="given-name" />
        </label>
      )}
      <label>
        Email
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          autoCapitalize="none"
          spellCheck={false}
        />
      </label>
      {mode !== 'recover' && (
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
      )}
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <button type="submit" disabled={busy}>
        {busy ? 'A processar…' : mode === 'recover' ? 'Enviar ligação' : title}
      </button>
      {mode === 'login' && (
        <button
          type="button"
          className="link"
          disabled={busy}
          onClick={() => {
            setError(null)
            setNotice(null)
            setMode('recover')
          }}
        >
          Esqueci-me da palavra-passe
        </button>
      )}
      <button
        type="button"
        className="link"
        disabled={busy}
        onClick={() => {
          setError(null)
          setNotice(null)
          setMode(mode === 'login' ? 'register' : 'login')
        }}
      >
        {mode === 'recover'
          ? 'Voltar a entrar'
          : mode === 'register'
            ? 'Já tenho conta'
            : 'Criar uma conta nova'}
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
      <button
        type="button"
        className="link"
        onClick={() => {
          setPlace(null)
          setManual(!manual)
        }}
      >
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
  const [reading, setReading] = useState<NatalReading | null>(null)
  const [readingError, setReadingError] = useState<string | null>(null)
  const sun = chart.bodies.find((b) => b.body === 'sun')
  const moon = chart.bodies.find((b) => b.body === 'moon')

  useEffect(() => {
    fetchNatalReading()
      .then((result) => {
        setReadingError(null)
        setReading(result)
      })
      .catch((error: unknown) => setReadingError(messageOf(error)))
  }, [])

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
      <table className="positions">
        <thead>
          <tr>
            <th scope="col">Corpo</th>
            <th scope="col">Signo</th>
            <th scope="col">Grau</th>
            <th scope="col">Casa</th>
          </tr>
        </thead>
        <tbody>
          {chart.bodies.map((b) => (
            <tr key={b.body}>
              <td>
                {BODIES[b.body] ?? b.body}
                {b.retrograde && <small className="retrograde-label">retrógrado</small>}
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
      <section aria-label="A tua leitura">
        <h3>A tua leitura</h3>
        {readingError && <p className="hint">{readingError}</p>}
        {!reading && !readingError && <p className="hint">A interpretar o mapa…</p>}
        {reading?.sections.map((section) => (
          <article key={section.id}>
            <h4>{section.title}</h4>
            {section.text
              .split(/\n{2,}/)
              .filter(Boolean)
              .map((paragraph, index) => (
                <p key={index}>{paragraph}</p>
              ))}
          </article>
        ))}
      </section>
    </section>
  )
}

function BirthSummary({ birth }: { birth: BirthProfile }) {
  const formattedDate = new Intl.DateTimeFormat('pt-PT', {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(new Date(`${birth.birth_date}T12:00:00Z`))
  return (
    <section className="card" aria-label="Dados de nascimento">
      <h2>Dados de nascimento</h2>
      <dl>
        <div>
          <dt>Data</dt>
          <dd>{formattedDate}</dd>
        </div>
        <div>
          <dt>Hora</dt>
          <dd>{birth.birth_time.slice(0, 5)}</dd>
        </div>
        <div>
          <dt>Local</dt>
          <dd>{birth.place_name}</dd>
        </div>
        <div>
          <dt>Fuso horário</dt>
          <dd>{birth.zone}</dd>
        </div>
      </dl>
    </section>
  )
}

function ProfileActions({ onDone }: { onDone: () => unknown }) {
  const [error, setError] = useState<string | null>(null)
  return (
    <section className="card account-actions" aria-label="Conta">
      {error && <p role="alert">{error}</p>}
      <button
        type="button"
        onClick={() =>
          void logout()
            .then(onDone)
            .catch((err: unknown) => setError(messageOf(err)))
        }
      >
        Sair
      </button>
      <button
        type="button"
        className="danger"
        onClick={() => {
          if (!window.confirm('Queres mesmo apagar a conta? Esta ação é irreversível.')) return
          void deleteAccount()
            .then(onDone)
            .catch((err: unknown) => setError(messageOf(err)))
        }}
      >
        Apagar conta
      </button>
    </section>
  )
}

async function loadState(): Promise<State> {
  try {
    const me = await fetchMe()
    let birth: BirthProfile
    try {
      birth = await fetchBirth()
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return { kind: 'needs-birth', me }
      throw err
    }
    try {
      return { kind: 'ready', me, chart: await fetchChart(), birth }
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
  const [tab, setTab] = useState<Tab>('today')
  const [resetToken, setResetToken] = useState(() =>
    new URLSearchParams(window.location.hash.slice(1)).get('recuperar'),
  )
  const [recovered, setRecovered] = useState(false)
  const contentRef = useRef<HTMLElement>(null)
  const refresh = useCallback(() => loadState().then(setState), [])

  useEffect(() => {
    void loadState().then(setState)
  }, [])
  useEffect(() => {
    if (contentRef.current) contentRef.current.scrollTop = 0
  }, [state.kind])

  useEffect(() => {
    const updateToken = () =>
      setResetToken(new URLSearchParams(window.location.hash.slice(1)).get('recuperar'))
    window.addEventListener('hashchange', updateToken)
    return () => window.removeEventListener('hashchange', updateToken)
  }, [])

  useEffect(() => {
    if (resetToken)
      window.history.replaceState(null, '', window.location.pathname + window.location.search)
  }, [resetToken])

  const signedIn = state.kind === 'needs-birth' || state.kind === 'ready'

  if (resetToken)
    return (
      <main>
        <div className="page">
          <h1>Arquivo do Universo</h1>
          <ResetPasswordForm
            token={resetToken}
            onClose={(changed) => {
              setResetToken(null)
              setRecovered(changed)
              void refresh()
            }}
          />
        </div>
      </main>
    )

  return (
    <>
      <main ref={contentRef}>
        <div className="page">
          <header>
            <h1>Arquivo do Universo</h1>
          </header>
          {signedIn && <p className="subtitle">Olá, {state.me.display_name}.</p>}
          {state.kind === 'loading' && <p>A consultar as estrelas…</p>}
          {state.kind === 'error' && <p role="alert">Servidor indisponível: {state.message}</p>}
          {state.kind === 'anonymous' && (
            <>
              {recovered && <p role="status">Palavra-passe atualizada. Já podes entrar.</p>}
              <AuthForm onDone={refresh} initialMode={recovered ? 'login' : 'register'} />
            </>
          )}
          {state.kind === 'needs-birth' && (
            <>
              <BirthForm
                key={state.problem ?? 'sem-problema'}
                onDone={refresh}
                problem={state.problem}
              />
              <ProfileActions onDone={refresh} />
            </>
          )}
          {state.kind === 'ready' && (
            <>
              {tab === 'today' && <Today me={state.me} onMoved={refresh} />}
              {tab === 'explore' && (
                <section className="card coming-soon">
                  <h2>Brevemente</h2>
                  <p>Ciclos, eclipses e o calendário do teu céu.</p>
                </section>
              )}
              {tab === 'journey' && (
                <section className="card coming-soon">
                  <h2>Brevemente</h2>
                  <p>Percursos de evolução e autodesenvolvimento.</p>
                </section>
              )}
              {tab === 'archive' && <Archive zone={state.me.residence_zone ?? state.birth.zone} />}
              {tab === 'profile' && (
                <>
                  <ChartSummary chart={state.chart} />
                  <BirthSummary birth={state.birth} />
                  <ProfileActions onDone={refresh} />
                </>
              )}
            </>
          )}
        </div>
      </main>
      {state.kind === 'ready' && (
        <nav className="bottom-nav" aria-label="Navegação principal">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              aria-current={tab === id ? 'page' : undefined}
              onClick={() => {
                setTab(id)
                if (contentRef.current) contentRef.current.scrollTop = 0
              }}
            >
              {label}
            </button>
          ))}
        </nav>
      )}
    </>
  )
}

export default App
