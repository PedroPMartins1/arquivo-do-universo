/** Keep the calculated longitude and move only crowded labels along that radius. */
export function planetLabelRadii(bodies: { body: string; longitude: number }[], baseRadius: number) {
  const placed: { x: number; y: number }[] = []
  const radii = new Map<string, number>()
  const candidates = [baseRadius, baseRadius + 34, baseRadius + 68, baseRadius - 34, baseRadius - 68]
  for (const body of bodies) {
    const angle = body.longitude * Math.PI / 180
    let best = candidates[0]
    let bestDistance = -1
    for (const radius of candidates) {
      const x = radius * Math.cos(angle)
      const y = radius * Math.sin(angle)
      const distance = placed.length ? Math.min(...placed.map((point) => Math.hypot(x - point.x, y - point.y))) : Infinity
      if (distance > bestDistance) { best = radius; bestDistance = distance }
      if (distance >= 34) { best = radius; break }
    }
    radii.set(body.body, best)
    placed.push({ x: best * Math.cos(angle), y: best * Math.sin(angle) })
  }
  return radii
}
