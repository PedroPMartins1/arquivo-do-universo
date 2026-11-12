import { useEffect, useState } from 'react'
import { type Place, searchPlaces } from './api'
import { describePlace } from './labels'


export function PlaceSearch({ onSelect }: { onSelect: (place: Place | null) => void }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Place[]>([])
  const [attribution, setAttribution] = useState('')
  const [chosen, setChosen] = useState<Place | null>(null)

  useEffect(() => {
    if (chosen || query.trim().length < 2) return
    const timer = setTimeout(() => {
      searchPlaces(query.trim())
        .then((found) => {
          setResults(found.results)
          setAttribution(found.attribution)
        })
        .catch(() => setResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [query, chosen])

  return (
    <div className="place-search">
      <label>
        Local de nascimento
        <input
          value={chosen ? describePlace(chosen) : query}
          onChange={(event) => {
            setChosen(null)
            onSelect(null)
            setQuery(event.target.value)
          }}
          placeholder="Escreve a cidade ou vila"
          autoComplete="off"
          role="combobox"
          aria-expanded={!chosen && results.length > 0}
          aria-controls="place-results"
          required
        />
      </label>
      {!chosen && query.trim().length >= 2 && results.length > 0 && (
        <ul id="place-results" role="listbox" aria-label="Localidades">
          {results.map((place) => (
            <li key={place.id} role="option" aria-selected={false}>
              <button
                type="button"
                className="option"
                onClick={() => {
                  setChosen(place)
                  onSelect(place)
                }}
              >
                {describePlace(place)}
              </button>
            </li>
          ))}
        </ul>
      )}
      {attribution && <p className="attribution">{attribution}</p>}
    </div>
  )
}
