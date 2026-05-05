import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useScripts() {
  return useQuery({
    queryKey: ['scripts'],
    queryFn: () => api.listScripts(),
  })
}

export function useVideos() {
  return useQuery({
    queryKey: ['videos'],
    queryFn: () => api.listVideos(),
  })
}

export function useStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: () => api.status(),
    refetchInterval: 10_000,
  })
}
