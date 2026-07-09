export function Sparkline({ closes, up, width = 72, height = 26 }: { closes: number[]; up: boolean; width?: number; height?: number }) {
  if (closes.length < 2) return <div style={{ width, height }} />
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const span = max - min || 1
  const pts = closes.map((c, i) => {
    const x = (i / (closes.length - 1)) * width
    const y = height - 2 - ((c - min) / span) * (height - 4)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const color = up ? '#34D399' : '#F87171'
  const id = up ? 'sp-u' : 'sp-d'
  return (
    <svg width={width} height={height} className="shrink-0">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth="1.5" />
      <polygon points={`0,${height} ${pts.join(' ')} ${width},${height}`} fill={`url(#${id})`} />
    </svg>
  )
}
