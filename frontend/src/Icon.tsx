export function Icon({ name }: { name: 'sun' | 'chart' | 'book' | 'user' | 'spark' }) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {name === 'sun' && <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>}
      {name === 'chart' && <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><path d="m5 6 13 12M12 3v4m9 5h-4M12 21v-4m-9-5h4M6 18l12-12" /></>}
      {name === 'book' && <><path d="M12 6c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1v15" /><path d="M6 9h3m-3 4h3m6-4h3m-3 4h3" /></>}
      {name === 'user' && <><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2" /></>}
      {name === 'spark' && <><path d="M12 2c1 6 4 9 10 10-6 1-9 4-10 10-1-6-4-9-10-10 6-1 9-4 10-10Z" /><path d="M20 2v4m-2-2h4" /></>}
    </svg>
  )
}
