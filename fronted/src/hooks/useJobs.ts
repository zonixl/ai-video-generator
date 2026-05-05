import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useJobs(status?: string) {
  return useQuery({
    queryKey: ['jobs', status],
    queryFn: () => api.listJobs(status),
    refetchInterval: 3000,
  })
}
