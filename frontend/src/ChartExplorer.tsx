import { useId, useRef, useState } from 'react'
import type { NatalChart } from './api'
import { ChartWheel } from './ChartWheel'
import { ASPECTS, BODIES, degrees, SIGNS, signName, signOfLongitude } from './labels'
import { ASPECT_GUIDE, BODY_GUIDE, HOUSE_GUIDE, SIGN_GUIDE } from './chartGuide'
import { sameSelection, signIndex, type ChartSelection } from './chartSelection'

type Category = 'body' | 'sign' | 'house' | 'aspect'
const CATEGORIES: { id: Category; name: string }[] = [
  { id: 'body', name: 'Planetas e pontos' },
  { id: 'sign', name: 'Signos' },
  { id: 'house', name: 'Casas' },
  { id: 'aspect', name: 'Aspetos' },
]
const bodyName = (id: string) => BODIES[id] ?? id
const aspectName = (chart: NatalChart, index: number) => {
  const aspect = chart.aspects[index]
  return `${bodyName(aspect.first)} em ${ASPECTS[aspect.kind] ?? aspect.kind} com ${bodyName(aspect.second)}`
}

export function ChartExplorer({ chart }: { chart: NatalChart }) {
  const firstBody = chart.bodies.find((body) => body.body === 'sun') ?? chart.bodies[0]
  const [selection, setSelection] = useState<ChartSelection | null>(firstBody ? { kind: 'body', id: firstBody.body } : null)
  const [category, setCategory] = useState<Category>('body')
  const detailRef = useRef<HTMLElement>(null)
  const mapRef = useRef<HTMLDivElement>(null)
  const detailId = useId()

  function choose(next: ChartSelection) {
    setSelection(next)
    setCategory(next.kind === 'angle' ? 'body' : next.kind)
    requestAnimationFrame(() => {
      detailRef.current?.focus({ preventScroll: true })
      detailRef.current?.scrollIntoView({ block: 'nearest' })
    })
  }

  function relation(item: ChartSelection, label: string) {
    return <button key={`${item.kind}-${label}`} type="button" className="chart-relation" onClick={() => choose(item)}>{label}</button>
  }

  const body = selection?.kind === 'body' ? chart.bodies.find((item) => item.body === selection.id) : undefined
  const house = selection?.kind === 'house' ? chart.houses.find((item) => item.house === selection.number) : undefined
  const sign = selection?.kind === 'sign' ? SIGN_GUIDE[selection.index] : undefined
  const aspect = selection?.kind === 'aspect' ? chart.aspects[selection.index] : undefined
  const angle = selection?.kind === 'angle' ? selection.id : undefined
  const relatedAspects = body ? chart.aspects.map((item, index) => ({ item, index })).filter(({ item }) => item.first === body.body || item.second === body.body) : []

  let title = 'Escolhe um elemento do teu mapa'
  if (body) title = `${bodyName(body.body)} em ${signName(body.sign)}`
  else if (house) title = `Casa ${house.house}`
  else if (sign && selection?.kind === 'sign') title = SIGNS[selection.index]
  else if (aspect && selection?.kind === 'aspect') title = aspectName(chart, selection.index)
  else if (angle) title = `${angle === 'ascendant' ? 'Ascendente' : 'Meio do Céu'} em ${signOfLongitude(chart.angles[angle])}`

  return <section className="chart-explorer" aria-label="Explorar o mapa natal">
    <p className="section-intro">Toca num elemento da roda ou escolhe nos botões abaixo. As ligações permitem seguir de um planeta para o seu signo, casa e aspetos.</p>
    <div ref={mapRef} tabIndex={-1} className="explorer-map">
      <ChartWheel chart={chart} selection={selection} onSelect={choose} />
    </div>
    <div className="chart-categories" role="group" aria-label="Tipo de elemento">
      {CATEGORIES.map(({ id, name }) => <button key={id} type="button" aria-pressed={category === id} aria-controls={`${detailId}-choices`} onClick={() => setCategory(id)}>{name}</button>)}
    </div>
    <div id={`${detailId}-choices`} className={`chart-choices ${category === 'aspect' ? 'aspect-choices' : ''}`} role="group" aria-label={`Escolher ${CATEGORIES.find((item) => item.id === category)!.name.toLocaleLowerCase('pt-PT')}`}>
      {category === 'body' && <>
        {chart.bodies.map((item) => <button type="button" key={item.body} aria-pressed={sameSelection(selection, { kind: 'body', id: item.body })} onClick={() => choose({ kind: 'body', id: item.body })}><strong>{bodyName(item.body)}</strong><span>{signName(item.sign)} · Casa {item.house}</span></button>)}
        {(['ascendant', 'midheaven'] as const).map((id) => <button type="button" key={id} aria-pressed={sameSelection(selection, { kind: 'angle', id })} onClick={() => choose({ kind: 'angle', id })}><strong>{id === 'ascendant' ? 'Ascendente' : 'Meio do Céu'}</strong><span>{signOfLongitude(chart.angles[id])}</span></button>)}
      </>}
      {category === 'sign' && SIGNS.map((name, index) => <button type="button" key={name} aria-pressed={sameSelection(selection, { kind: 'sign', index })} onClick={() => choose({ kind: 'sign', index })}><strong>{name}</strong><span>{SIGN_GUIDE[index].element} · {SIGN_GUIDE[index].mode}</span></button>)}
      {category === 'house' && chart.houses.map((item) => <button type="button" key={item.house} aria-pressed={sameSelection(selection, { kind: 'house', number: item.house })} onClick={() => choose({ kind: 'house', number: item.house })}><strong>Casa {item.house}</strong><span>{HOUSE_GUIDE[item.house - 1]}</span></button>)}
      {category === 'aspect' && chart.aspects.map((item, index) => <button type="button" key={`${item.first}-${item.second}-${item.kind}`} aria-pressed={sameSelection(selection, { kind: 'aspect', index })} onClick={() => choose({ kind: 'aspect', index })}><strong>{bodyName(item.first)} · {bodyName(item.second)}</strong><span>{ASPECTS[item.kind] ?? item.kind} · orbe {degrees(item.orb)}</span></button>)}
      {category === 'aspect' && chart.aspects.length === 0 && <p className="hint">Não há aspetos neste resultado com as tolerâncias de cálculo atuais.</p>}
    </div>
    <section id={detailId} ref={detailRef} tabIndex={-1} className="chart-detail" aria-label="Elemento selecionado">
      <p className="eyebrow">No teu mapa</p>
      <h3>{title}</h3>
      {body && <>
        <p className="chart-position">{degrees(body.degree_in_sign)} de {signName(body.sign)} · Casa {body.house}{body.retrograde ? ' · Retrógrado' : ''}</p>
        <h4>O que representa</h4>
        <p>{BODY_GUIDE[body.body]?.meaning ?? 'Este elemento faz parte do resultado calculado do teu mapa.'}</p>
        <h4>Como explorar esta posição</h4>
        <p>O planeta ou ponto indica o tema, o signo descreve um modo de expressão e a casa situa uma área de vida. Consulta cada ligação para compreender estas camadas em conjunto.</p>
        <div className="chart-relations" aria-label="Signo e casa deste elemento">
          {relation({ kind: 'sign', index: signIndex(body.longitude) }, `Signo ${signName(body.sign)}`)}
          {chart.houses.some((item) => item.house === body.house) && relation({ kind: 'house', number: body.house }, `Casa ${body.house} · ${HOUSE_GUIDE[body.house - 1]}`)}
        </div>
        {body.retrograde && <p className="hint">Retrógrado descreve um movimento aparente visto da Terra no nascimento. Não é, por si só, uma indicação negativa.</p>}
        <h4>Ligações a outros elementos</h4>
        <div className="chart-relations">{relatedAspects.map(({ index }) => relation({ kind: 'aspect', index }, aspectName(chart, index)))}</div>
        {relatedAspects.length === 0 && <p className="hint">Não há aspetos calculados para este elemento nas tolerâncias atuais.</p>}
        {BODY_GUIDE[body.body] && <p className="question">{BODY_GUIDE[body.body].question}</p>}
      </>}
      {sign && selection?.kind === 'sign' && <>
        <p className="chart-position">Elemento {sign.element.toLocaleLowerCase('pt-PT')} · Qualidade {sign.mode.toLocaleLowerCase('pt-PT')}</p>
        <h4>O que representa</h4><p>{sign.meaning}</p>
        <h4>Elementos do teu mapa neste signo</h4>
        <div className="chart-relations">{chart.bodies.filter((item) => signIndex(item.longitude) === selection.index).map((item) => relation({ kind: 'body', id: item.body }, `${bodyName(item.body)} · Casa ${item.house}`))}</div>
        {!chart.bodies.some((item) => signIndex(item.longitude) === selection.index) && <p className="hint">Não há planetas ou pontos calculados neste signo. Isso não significa ausência deste tema na tua vida.</p>}
        <p className="hint">Um signo é uma camada do mapa, não uma descrição completa de uma pessoa.</p>
      </>}
      {house && <>
        <p className="chart-position">Início da casa: {degrees(((house.longitude % 30) + 30) % 30)} de {signOfLongitude(house.longitude)}</p>
        <h4>Área de vida</h4><p>{HOUSE_GUIDE[house.house - 1]}</p>
        <div className="chart-relations">{relation({ kind: 'sign', index: signIndex(house.longitude) }, `Signo no início da casa: ${signOfLongitude(house.longitude)}`)}</div>
        <h4>Elementos nesta casa</h4>
        <div className="chart-relations">{chart.bodies.filter((item) => item.house === house.house).map((item) => relation({ kind: 'body', id: item.body }, `${bodyName(item.body)} em ${signName(item.sign)}`))}</div>
        {!chart.bodies.some((item) => item.house === house.house) && <p className="hint">Esta casa não tem planetas ou pontos no resultado atual. Uma casa vazia não significa uma área de vida inexistente.</p>}
      </>}
      {aspect && <>
        <p className="chart-position">{ASPECT_GUIDE[aspect.kind] ? `Ângulo de referência: ${ASPECT_GUIDE[aspect.kind].angle}° · ` : ''}Orbe: {degrees(aspect.orb)}</p>
        <h4>O que representa</h4><p>{ASPECT_GUIDE[aspect.kind]?.meaning ?? 'Uma relação angular identificada pelo cálculo entre dois elementos do mapa.'}</p>
        <p className="hint">O orbe é o desvio em relação ao ângulo exato do aspeto. A lista mostra apenas as relações presentes no resultado calculado.</p>
        <h4>Explorar os dois elementos</h4>
        <div className="chart-relations">{[aspect.first, aspect.second].filter((id) => chart.bodies.some((item) => item.body === id)).map((id) => relation({ kind: 'body', id }, bodyName(id)))}</div>
        <p className="question">Como reconheces a relação entre estes dois temas na tua experiência?</p>
      </>}
      {angle && <>
        <p className="chart-position">{degrees(((chart.angles[angle] % 30) + 30) % 30)} de {signOfLongitude(chart.angles[angle])}</p>
        <h4>O que representa</h4>
        <p>{angle === 'ascendant' ? 'O Ascendente é o ponto da eclíptica que se eleva no horizonte oriental no nascimento. Na leitura astrológica, associa-se à apresentação pessoal e à forma de abordar novas experiências.' : 'O Meio do Céu é um ângulo do mapa associado, na leitura astrológica, à vocação e à vida pública. Não determina uma profissão.'}</p>
        <div className="chart-relations">{relation({ kind: 'sign', index: signIndex(chart.angles[angle]) }, `Explorar ${signOfLongitude(chart.angles[angle])}`)}</div>
      </>}
      {!selection && <p>Usa a roda ou os botões para começar.</p>}
      <p className="chart-education">Guia simbólico e educativo. Estas explicações não substituem a leitura global do teu mapa.</p>
      <button type="button" className="link" onClick={() => { mapRef.current?.focus({ preventScroll: true }); mapRef.current?.scrollIntoView({ block: 'start' }) }}>Voltar à roda do mapa</button>
    </section>
    <details className="chart-help">
      <summary>Como ler os elementos e as ligações</summary>
      <p>Os símbolos representam planetas e pontos. A faixa exterior mostra os signos; os números identificam as casas; as linhas interiores representam aspetos. O destaque acompanha o elemento selecionado. Quando dois símbolos ficam próximos, uma linha fina liga o símbolo deslocado à sua posição calculada.</p>
      <p>Os dados vêm do teu mapa calculado. As descrições são um guia editorial de linguagem astrológica, separado da interpretação personalizada apresentada abaixo.</p>
      <a href="https://www.astro.com/astrology/in_intro_e.htm" target="_blank" rel="noopener noreferrer">Referência educativa: Astrodienst</a>
    </details>
  </section>
}
