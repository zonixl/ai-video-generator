import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId),
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'running' || s === 'pending' ? 2000 : false
    },
    enabled: !!jobId,
  })
}
