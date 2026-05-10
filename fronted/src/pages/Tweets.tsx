import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Eye, ImageIcon, RefreshCw, Download, Pencil, Save } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { StaggerList, StaggerItem } from '@/components/StaggerList'
import { ListSkeleton } from '@/components/LoadingSkeleton'
import { useTweets } from '@/hooks/useScripts'
import { api } from '@/lib/api'
import { toast } from 'sonner'

export default function Tweets() {
  const { data: tweets, isLoading, refetch } = useTweets()
  const [preview, setPreview] = useState<{ name: string; article: string; images: string[] } | null>(null)
  const [previewContent, setPreviewContent] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const handlePreview = async (tweet: { name: string; article: string; images: string[] }) => {
    setPreview(tweet)
    setPreviewContent('')
    setEditing(false)
    setEditContent('')
    if (!tweet.article) return
    setPreviewLoading(true)
    try {
      const res = await fetch(`/api/files/${encodeURIComponent(tweet.article)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setPreviewContent(await res.text())
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
    if (!preview?.article) return
    setSaving(true)
    try {
      await api.saveTweet(preview.article, editContent)
      setPreviewContent(editContent)
      setEditing(false)
      toast.success('推文已保存')
      refetch()
    } catch (e) {
      toast.error(`保存失败: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  const closeDialog = () => {
    setPreview(null)
    setPreviewContent('')
    setEditing(false)
    setEditContent('')
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">推文库</h1>
        <p className="mt-1 text-muted-foreground">浏览已生成的图文推文</p>
      </div>

      {isLoading ? (
        <ListSkeleton count={6} />
      ) : !tweets?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
            <FileText className="h-12 w-12" />
            <p>暂无推文</p>
            <Button variant="outline" onClick={() => window.location.href = '/produce'}>
              去生成推文
            </Button>
          </CardContent>
        </Card>
      ) : (
        <StaggerList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tweets.map((t) => (
            <StaggerItem key={t.path}>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Card
                  className="cursor-pointer transition-shadow hover:shadow-md group"
                  onClick={() => handlePreview(t)}
                >
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="truncate text-sm font-medium flex-1">{t.name}</span>
                      <Eye className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{new Date(t.created_at * 1000).toLocaleDateString('zh-CN')}</span>
                      {t.images.length > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          <ImageIcon className="mr-1 h-3 w-3" />
                          {t.images.length} 张配图
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </StaggerItem>
          ))}
        </StaggerList>
      )}

      {/* 推文预览 / 编辑弹窗 */}
      <Dialog open={!!preview} onOpenChange={(open) => { if (!open) closeDialog() }}>
        <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {preview?.name}
            </DialogTitle>
            <DialogDescription>
              {editing ? '编辑推文内容，点击保存后写入文件' : '推文内容预览'}
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
              <div className="space-y-4">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed bg-muted/50 rounded-lg p-4 max-h-[50vh] overflow-auto">
                  {previewContent || '无内容'}
                </pre>
                {/* 配图预览 */}
                {preview?.images && preview.images.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">配图</p>
                    <div className="grid grid-cols-3 gap-2">
                      {preview.images.map((img) => (
                        <a
                          key={img}
                          href={`/api/files/${encodeURIComponent(img)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="aspect-square rounded-lg overflow-hidden bg-muted hover:opacity-80 transition-opacity"
                        >
                          <img
                            src={`/api/files/${encodeURIComponent(img)}`}
                            className="w-full h-full object-cover"
                            alt=""
                          />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
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
              !previewLoading && preview?.article && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => window.open(`/api/files/${encodeURIComponent(preview.article)}`, '_blank')}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    下载 MD
                  </Button>
                  <Button variant="outline" onClick={handleEdit}>
                    <Pencil className="mr-2 h-4 w-4" />
                    编辑
                  </Button>
                </>
              )
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
