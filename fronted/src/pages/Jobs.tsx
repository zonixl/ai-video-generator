import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, CheckCircle2, XCircle, Loader2, X, Ban } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { JobBadge } from '@/components/JobBadge'
import { StaggerList, StaggerItem } from '@/components/StaggerList'
import { ListSkeleton } from '@/components/LoadingSkeleton'
import { useJobs } from '@/hooks/useJobs'
import { api } from '@/lib/api'
import { toast } from 'sonner'

const filters = [
  { label: '全部', value: undefined },
  { label: '运行中', value: 'running' },
  { label: '等待中', value: 'pending' },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' },
]

function timeAgo(ts: number) {
  const diff = Math.floor(Date.now() / 1000 - ts)
  if (diff < 60) return `${diff}s 前`
  if (diff < 3600) return `${Math.floor(diff / 60)}min 前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h 前`
  return `${Math.floor(diff / 86400)}d 前`
}

export default function Jobs() {
  const [filter, setFilter] = useState<string | undefined>()
  const { data: jobs, isLoading, refetch } = useJobs(filter)

  const handleCancel = async (jobId: string) => {
    try {
      await api.cancelJob(jobId)
      toast.success('任务已取消')
      refetch()
    } catch (e) {
      toast.error(`取消失败: ${(e as Error).message}`)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">任务中心</h1>
        <p className="mt-1 text-muted-foreground">实时查看异步任务状态</p>
      </div>

      {/* 过滤器 */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <motion.div key={f.label} whileTap={{ scale: 0.95 }}>
            <Badge
              variant={filter === f.value ? 'default' : 'outline'}
              className="cursor-pointer px-3 py-1"
              onClick={() => setFilter(f.value)}
            >
              {f.label}
            </Badge>
          </motion.div>
        ))}
      </div>

      {/* 任务列表 */}
      {isLoading ? (
        <ListSkeleton count={5} />
      ) : !jobs?.length ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
            暂无{filter ? '匹配的' : ''}任务
          </CardContent>
        </Card>
      ) : (
        <AnimatePresence mode="popLayout">
          <StaggerList className="space-y-3">
            {jobs.map((job) => (
              <StaggerItem key={job.id}>
                <motion.div layout>
                  <Card>
                    <CardContent className="flex items-center justify-between py-4 px-5">
                      <div className="flex items-center gap-4 min-w-0 flex-1">
                        <div className="shrink-0">
                          {job.status === 'running' && (
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                            >
                              <Loader2 className="h-5 w-5 text-blue-500" />
                            </motion.div>
                          )}
                          {job.status === 'success' && (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          )}
                          {job.status === 'failed' && (
                            <XCircle className="h-5 w-5 text-red-500" />
                          )}
                          {job.status === 'pending' && (
                            <Clock className="h-5 w-5 text-gray-400" />
                          )}
                          {job.status === 'cancelled' && (
                            <Ban className="h-5 w-5 text-orange-500" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{job.type}</span>
                            <JobBadge status={job.status} />
                          </div>
                          <div className="mt-1 text-xs text-muted-foreground truncate">
                            {job.id}
                          </div>
                          {job.status === 'failed' && job.error && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              className="mt-1 text-xs text-destructive truncate"
                            >
                              {job.error}
                            </motion.div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4 shrink-0">
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {timeAgo(job.created_at)}
                        </span>
                        {(job.status === 'running' || job.status === 'pending') && (
                          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 px-2 text-xs text-destructive hover:text-destructive"
                              onClick={() => handleCancel(job.id)}
                            >
                              <X className="mr-1 h-3 w-3" />
                              取消
                            </Button>
                          </motion.div>
                        )}
                      </div>
                    </CardContent>
                    {job.status === 'running' && (
                      <div className="px-5 pb-3">
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                        >
                          <Progress value={null} className="h-1" />
                        </motion.div>
                      </div>
                    )}
                  </Card>
                </motion.div>
              </StaggerItem>
            ))}
          </StaggerList>
        </AnimatePresence>
      )}
    </div>
  )
}
