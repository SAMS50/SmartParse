import {useEffect, useRef} from 'react'

/** Pointer and keyboard resizing without remounting either neighboring panel. */
export function PanelDivider({axis, label, value, min, max, step, onChange, onDrag}: {
  axis: 'vertical' | 'horizontal'; label: string; value: number; min: number; max: number;
  step: number; onChange: (value: number) => void; onDrag: (event: PointerEvent) => void;
}) {
  const cleanup = useRef(() => {})
  useEffect(() => () => cleanup.current(), [])
  return <div className={`panel-divider ${axis}`} role="separator" aria-label={label}
    aria-orientation={axis} aria-valuenow={Math.round(value)} aria-valuemin={min} aria-valuemax={max}
    title={axis === 'vertical' ? 'Drag or use Left / Right to resize' : 'Drag or use Up / Down to resize'}
    tabIndex={0} onKeyDown={event => {
      let next: number | undefined
      if (event.key === 'Home') next = min
      if (event.key === 'End') next = max
      if (event.key === (axis === 'vertical' ? 'ArrowRight' : 'ArrowUp')) next = value + step
      if (event.key === (axis === 'vertical' ? 'ArrowLeft' : 'ArrowDown')) next = value - step
      if (next !== undefined) {event.preventDefault(); onChange(Math.max(min, Math.min(max, next)))}
    }} onPointerDown={event => {
      if (event.button !== 0) return
      event.preventDefault(); cleanup.current()
      event.currentTarget.setPointerCapture?.(event.pointerId)
      const move = (e: PointerEvent) => {if (e.pointerId === event.pointerId) onDrag(e)}
      const stop = () => {
        window.removeEventListener('pointermove', move)
        window.removeEventListener('pointerup', stop)
        window.removeEventListener('pointercancel', stop)
        document.body.classList.remove('resizing-panels')
      }
      cleanup.current = stop
      document.body.classList.add('resizing-panels')
      window.addEventListener('pointermove', move)
      window.addEventListener('pointerup', stop)
      window.addEventListener('pointercancel', stop)
    }}><span/></div>
}
