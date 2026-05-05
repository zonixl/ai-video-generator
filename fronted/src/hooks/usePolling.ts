import { useEffect, useRef, useState } from 'react'

export function usePolling<T>(fn: () => Promise<T>, intervalMs: number = 3000) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const result = await fnRef.current()
        if (!cancelled) setData(result)
      } catch (e) {
        if (!cancelled) setError(e as Error)
      }
    }
    tick()
    const id = setInterval(tick, intervalMs)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [intervalMs])

  return { data, error }
}
