import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Sparkles, Play, RefreshCw, Upload, Eye, Pencil, Save } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { StaggerList, StaggerItem } from '@/components/StaggerList'
import { ListSkeleton } from '@/components/LoadingSkeleton'
import { useScripts } from '@/hooks/useScripts'
import { api } from '@/lib/api'
import { toast } from 'sonner'

export default function Scripts() {
  const { data: scripts, isLoading, refetch } = useScripts()
  const [topic, setTopic] = useState('')
  const [style, setStyle] = useState('专业但不枯燥，适合短视频口播')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  // 摄入文本
  const [ingestText, setIngestText] = useState('')
  const [ingestName, setIngestName] = useState('')
  const [ingesting, setIngesting] = useState(false)

  // 文案预览 / 编辑
  const [previewFile, setPreviewFile] = useState<{ name: string; path: string } | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('请输入话题')
      return
    }
    setGenerating(true)
    setResult(null)
    try {
      const res = await api.generate(topic, style)
      setResult(res.script)
      toast.success('文案生成成功')
      refetch()
    } catch (e) {
      toast.error(`生成失败: ${(e as Error).message}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleIngest = async () => {
    if (!ingestText.trim()) {
      toast.error('请输入文本内容')
      return
    }
    if (ingestText.trim().length < 10) {
      toast.error('文本内容太短（至少 10 个字符）')
      return
    }
    setIngesting(true)
    try {
      const res = await api.ingestText(ingestText, ingestName || undefined)
      toast.success(`文本已摄入知识库：${res.message}`)
      setIngestText('')
      setIngestName('')
      refetch()
    } catch (e) {
      toast.error(`摄入失败: ${(e as Error).message}`)
    } finally {
      setIngesting(false)
    }
  }

  const handlePreview = async (file: { name: string; path: string }) => {
    setPreviewFile(file)
    setPreviewContent('')
    setEditing(false)
    setPreviewLoading(true)
    try {
      const res = await fetch(`/api/files/${encodeURIComponent(file.path)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const text = await res.text()
      setPreviewContent(text)
    } catch (e) {
      setPreviewContent(`加载失败: ${(e as Error).message}`)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleEdit = () => {
    setEditContent(previewContent)
    setEditing(true)
  }

  const handleCancelEdit = () => {
    setEditing(false)
    setEditContent('')
  }

  const handleSave = async () => {
    if (!previewFile) return
    setSaving(true)
    try {
      await api.saveScript(previewFile.path, editContent)
      setPreviewContent(editContent)
      setEditing(false)
      toast.success('文案已保存')
      refetch()
    } catch (e) {
      toast.error(`保存失败: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  const closeDialog = () => {
    setPreviewFile(null)
    setPreviewContent('')
    setEditing(false)
    setEditContent('')
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">文案管理</h1>
        <p className="mt-1 text-muted-foreground">生成、摄入、查看短视频文案</p>
      </div>

      {/* 生成区 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4" />
            生成新文案
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Input
              placeholder="输入话题，如：AI 的发展趋势"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
              className="flex-1"
            />
            <Input
              placeholder="文案风格"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-64"
            />
            <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
              <Button onClick={handleGenerate} disabled={generating}>
                {generating ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                生成
              </Button>
            </motion.div>
          </div>

          {result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.3 }}
            >
              <Textarea
                value={result}
                readOnly
                className="min-h-[200px] font-mono text-sm"
              />
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* 摄入文本区 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Upload className="h-4 w-4" />
            摄入文本到知识库
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            直接输入文本内容，AI 自动整理后存入知识库，可用于后续文案生成参考。
          </p>
          <div className="flex gap-3">
            <Input
              placeholder="来源名称（可选，如：课程笔记）"
              value={ingestName}
              onChange={(e) => setIngestName(e.target.value)}
              className="w-48"
            />
          </div>
          <Textarea
            placeholder="粘贴文本内容..."
            value={ingestText}
            onChange={(e) => setIngestText(e.target.value)}
            className="min-h-[150px]"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {ingestText.length} 个字符
            </span>
            <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
              <Button onClick={handleIngest} disabled={ingesting || ingestText.trim().length < 10}>
                {ingesting ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                摄入知识库
              </Button>
            </motion.div>
          </div>
        </CardContent>
      </Card>

      {/* 文案列表 */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">已有文案</h2>
          <Badge variant="secondary">{scripts?.length ?? 0} 个文件</Badge>
        </div>
        {isLoading ? (
          <ListSkeleton count={4} />
        ) : !scripts?.length ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
              暂无文案，输入话题开始生成
            </CardContent>
          </Card>
        ) : (
          <StaggerList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {scripts.map((s) => (
              <StaggerItem key={s.path}>
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                  <Card
                    className="cursor-pointer transition-shadow hover:shadow-md group"
                    onClick={() => handlePreview(s)}
                  >
                    <CardContent className="p-5">
                      <div className="mb-2 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="truncate text-sm font-medium flex-1">{s.name}</span>
                        <Eye className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{(s.size / 1024).toFixed(1)} KB</span>
                        <span>
                          {new Date(s.modified * 1000).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </StaggerItem>
            ))}
          </StaggerList>
        )}
      </div>

      {/* 文案预览 / 编辑弹窗 */}
      <Dialog open={!!previewFile} onOpenChange={(open) => { if (!open) closeDialog() }}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {previewFile?.name}
            </DialogTitle>
            <DialogDescription>
              {editing ? '编辑文案内容，点击保存后写入文件' : '文案内容预览'}
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto min-h-0">
            {previewLoading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : editing ? (
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[50vh] max-h-[60vh] font-mono text-sm leading-relaxed"
              />
            ) : (
              <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed bg-muted/50 rounded-lg p-4 max-h-[60vh] overflow-auto">
                {previewContent}
              </pre>
            )}
          </div>
          {/* 底部操作栏 */}
          <div className="flex justify-end gap-2 pt-2 border-t">
            {editing ? (
              <>
                <Button variant="outline" onClick={handleCancelEdit}>
                  取消
                </Button>
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Button onClick={handleSave} disabled={saving}>
                    {saving ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="mr-2 h-4 w-4" />
                    )}
                    保存
                  </Button>
                </motion.div>
              </>
            ) : (
              !previewLoading && (
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="outline" onClick={handleEdit}>
                    <Pencil className="mr-2 h-4 w-4" />
                    编辑
                  </Button>
                </motion.div>
              )
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
