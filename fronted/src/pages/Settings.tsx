import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings2, Trash2, Bomb, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useStatus } from '@/hooks/useScripts'
import { toast } from 'sonner'

export default function Settings() {
  const { data: status, refetch } = useStatus()
  const [clearing, setClearing] = useState(false)
  const [nuking, setNuking] = useState(false)

  const handleClear = async () => {
    setClearing(true)
    try {
      await fetch('/api/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      })
      toast.success('知识库已清空')
      refetch()
    } catch (e) {
      toast.error(`操作失败: ${(e as Error).message}`)
    } finally {
      setClearing(false)
    }
  }

  const handleNuke = async () => {
    setNuking(true)
    try {
      await fetch('/api/nuke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      })
      toast.success('所有数据已清除')
      refetch()
    } catch (e) {
      toast.error(`操作失败: ${(e as Error).message}`)
    } finally {
      setNuking(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">系统设置</h1>
        <p className="mt-1 text-muted-foreground">系统状态和管理操作</p>
      </div>

      {/* 系统状态 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Settings2 className="h-4 w-4" />
            系统状态
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <div className="text-sm text-muted-foreground">知识库集合</div>
              <div className="mt-1 font-medium">{status?.collection ?? '-'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">文档数量</div>
              <div className="mt-1 font-medium">{status?.doc_count ?? '-'}</div>
            </div>
          </div>
          <div>
            <div className="mb-2 text-sm text-muted-foreground">模型实例</div>
            <div className="flex flex-wrap gap-2">
              {(status?.instances ?? []).map((inst) => (
                <Badge key={inst} variant="secondary">{inst}</Badge>
              ))}
              {!status?.instances?.length && (
                <span className="text-sm text-muted-foreground">无</span>
              )}
            </div>
          </div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新状态
            </Button>
          </motion.div>
        </CardContent>
      </Card>

      <Separator />

      {/* 危险操作 */}
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-destructive">
            <Bomb className="h-4 w-4" />
            危险操作
          </CardTitle>
          <CardDescription>以下操作不可逆，请谨慎使用</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
            <Button
              variant="outline"
              onClick={handleClear}
              disabled={clearing}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {clearing ? '清空中...' : '清空知识库'}
            </Button>
          </motion.div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
            <Button
              variant="destructive"
              onClick={handleNuke}
              disabled={nuking}
            >
              <Bomb className="mr-2 h-4 w-4" />
              {nuking ? '清除中...' : '清除所有数据'}
            </Button>
          </motion.div>
        </CardContent>
      </Card>
    </div>
  )
}
