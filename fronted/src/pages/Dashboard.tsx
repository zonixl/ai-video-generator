import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText,
  Video,
  Upload,
  ListTodo,
  Activity,
  Database,
  Cpu,
  RefreshCw,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { JobBadge } from '@/components/JobBadge'
import { StaggerList, StaggerItem } from '@/components/StaggerList'
import { ListSkeleton } from '@/components/LoadingSkeleton'
import { useStatus } from '@/hooks/useScripts'
import { useJobs } from '@/hooks/useJobs'
import { useJob } from '@/hooks/useJob'
import { api } from '@/lib/api'
import { toast } from 'sonner'

const quickActions = [
  { label: '生成文案', desc: '根据话题生成短视频文案', to: '/scripts', icon: FileText, color: 'bg-blue-500' },
  { label: '制作视频', desc: '文案到视频全链路', to: '/produce', icon: Video, color: 'bg-purple-500' },
  { label: '查看任务', desc: '实时任务状态', to: '/jobs', icon: ListTodo, color: 'bg-orange-500' },
]

function timeAgo(ts: number) {
  const diff = Math.floor(Date.now() / 1000 - ts)
  if (diff < 60) return `${diff}s 前`
  if (diff < 3600) return `${Math.floor(diff / 60)}min 前`
  return `${Math.floor(diff / 3600)}h 前`
}

export default function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus()
  const { data: jobs, isLoading: jobsLoading, refetch: refetchJobs } = useJobs()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [ingestJobId, setIngestJobId] = useState('')
  const { data: ingestJob } = useJob(ingestJobId)

  const recentJobs = (jobs ?? []).slice(0, 5)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setIngestJobId('')
    try {
      const res = await api.ingest(file)
      setIngestJobId(res.job_id)
      toast.success(`已上传：${file.name}`)
      refetchJobs()
    } catch (err) {
      toast.error(`上传失败：${(err as Error).message}`)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统总览</h1>
        <p className="mt-1 text-muted-foreground">AI 内容生产系统 — 短视频自动生成</p>
      </div>

      {/* 系统状态 */}
      <StaggerList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StaggerItem>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                知识库
              </CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statusLoading ? (
                <div className="h-8 w-16 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold">{status?.doc_count ?? 0}</div>
              )}
              <p className="text-xs text-muted-foreground">文档片段</p>
            </CardContent>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                模型实例
              </CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statusLoading ? (
                <div className="h-8 w-16 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold">{status?.instances?.length ?? 0}</div>
              )}
              <p className="text-xs text-muted-foreground">已配置</p>
            </CardContent>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                任务队列
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {jobsLoading ? (
                <div className="h-8 w-16 animate-pulse rounded bg-muted" />
              ) : (
                <div className="text-2xl font-bold">
                  {(jobs ?? []).filter((j) => j.status === 'running').length}
                </div>
              )}
              <p className="text-xs text-muted-foreground">运行中</p>
            </CardContent>
          </Card>
        </StaggerItem>
      </StaggerList>

      {/* 快捷操作 */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">快捷操作</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* 摄入音频 - 直接选文件 */}
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Card
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => fileInputRef.current?.click()}
            >
              <CardContent className="flex items-start gap-4 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-500">
                  {uploading ? (
                    <RefreshCw className="h-5 w-5 text-white animate-spin" />
                  ) : (
                    <Upload className="h-5 w-5 text-white" />
                  )}
                </div>
                <div>
                  <div className="font-medium">摄入音频</div>
                  <div className="text-sm text-muted-foreground">
                    {uploading ? '上传中...' : '选择音频文件导入知识库'}
                  </div>
                </div>
              </CardContent>
            </Card>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.flac,.ogg,.aac"
              className="hidden"
              onChange={handleFileSelect}
            />
          </motion.div>

          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <motion.div key={action.label} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Link to={action.to}>
                  <Card className="cursor-pointer transition-shadow hover:shadow-md">
                    <CardContent className="flex items-start gap-4 p-5">
                      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${action.color}`}>
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <div className="font-medium">{action.label}</div>
                        <div className="text-sm text-muted-foreground">{action.desc}</div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            )
          })}
        </div>

        {/* 摄入任务状态 */}
        {ingestJobId && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4"
          >
            <Card>
              <CardContent className="flex items-center justify-between py-3 px-5">
                <div className="flex items-center gap-3">
                  <JobBadge status={ingestJob?.status ?? 'pending'} />
                  <div>
                    <div className="text-sm font-medium">音频摄入</div>
                    <div className="text-xs text-muted-foreground">{ingestJobId}</div>
                  </div>
                </div>
                <div>
                  {(ingestJob?.status === 'success') && (
                    <Badge variant="secondary">+{ingestJob?.result?.chunks ?? '?'} 片段</Badge>
                  )}
                  {ingestJob?.status === 'failed' && (
                    <span className="text-xs text-destructive">{ingestJob?.error}</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      {/* 最近任务 */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">最近任务</h2>
          <Link to="/jobs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            查看全部 →
          </Link>
        </div>
        {jobsLoading ? (
          <ListSkeleton count={3} />
        ) : recentJobs.length === 0 ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
              暂无任务记录
            </CardContent>
          </Card>
        ) : (
          <StaggerList className="space-y-2">
            {recentJobs.map((job) => (
              <StaggerItem key={job.id}>
                <Card>
                  <CardContent className="flex items-center justify-between py-3 px-5">
                    <div className="flex items-center gap-3">
                      <JobBadge status={job.status} />
                      <div>
                        <div className="text-sm font-medium">{job.type}</div>
                        <div className="text-xs text-muted-foreground">{job.id}</div>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {timeAgo(job.created_at)}
                    </div>
                  </CardContent>
                </Card>
              </StaggerItem>
            ))}
          </StaggerList>
        )}
      </div>
    </div>
  )
}
