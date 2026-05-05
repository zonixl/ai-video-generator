import { useState } from 'react'
import { motion } from 'framer-motion'
import { Film, Play, FolderOpen } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { StaggerList, StaggerItem } from '@/components/StaggerList'
import { ListSkeleton } from '@/components/LoadingSkeleton'
import { useVideos } from '@/hooks/useScripts'

export default function Videos() {
  const { data: videos, isLoading } = useVideos()
  const [previewVideo, setPreviewVideo] = useState<{ job_id: string; video: string } | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">视频库</h1>
        <p className="mt-1 text-muted-foreground">浏览已生成的视频</p>
      </div>

      {isLoading ? (
        <ListSkeleton count={6} />
      ) : !videos?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
            <Film className="h-12 w-12" />
            <p>暂无视频</p>
            <Button variant="outline" onClick={() => window.location.href = '/produce'}>
              去制作视频
            </Button>
          </CardContent>
        </Card>
      ) : (
        <StaggerList className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {videos.map((v) =>
            v.videos.length > 0 ? (
              v.videos.map((videoPath, idx) => (
                <StaggerItem key={`${v.job_id}-${idx}`}>
                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Card
                      className="overflow-hidden transition-shadow hover:shadow-lg cursor-pointer group"
                      onClick={() => setPreviewVideo({ job_id: v.job_id, video: videoPath })}
                    >
                      {/* 视频缩略图区域 */}
                      <div className="relative aspect-video bg-muted flex items-center justify-center">
                        <video
                          className="absolute inset-0 w-full h-full object-cover"
                          src={`/api/files/${encodeURIComponent(videoPath)}`}
                          preload="metadata"
                          muted
                          playsInline
                          onMouseEnter={(e) => { (e.target as HTMLVideoElement).play().catch(() => {}) }}
                          onMouseLeave={(e) => { (e.target as HTMLVideoElement).pause(); (e.target as HTMLVideoElement).currentTime = 0 }}
                        />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-colors pointer-events-none">
                          <motion.div
                            className="flex items-center justify-center h-12 w-12 rounded-full bg-white/20 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Play className="h-6 w-6 text-white ml-0.5" />
                          </motion.div>
                        </div>
                      </div>
                      <CardContent className="p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <span className="truncate text-sm font-medium">{v.job_id}</span>
                          <Badge variant="secondary" className="shrink-0">
                            {videoPath.split('.').pop()}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <FolderOpen className="h-3 w-3" />
                          <span className="truncate">{videoPath}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                </StaggerItem>
              ))
            ) : (
              <StaggerItem key={v.job_id}>
                <Card className="overflow-hidden">
                  <div className="relative aspect-video bg-muted flex items-center justify-center">
                    <Film className="h-12 w-12 text-muted-foreground/30" />
                  </div>
                  <CardContent className="p-4">
                    <span className="truncate text-sm font-medium">{v.job_id}</span>
                    <p className="text-xs text-muted-foreground mt-1">无视频文件</p>
                  </CardContent>
                </Card>
              </StaggerItem>
            )
          )}
        </StaggerList>
      )}

      {/* 视频预览弹窗 */}
      <Dialog open={!!previewVideo} onOpenChange={(open) => { if (!open) setPreviewVideo(null) }}>
        <DialogContent className="sm:max-w-3xl p-0 overflow-hidden">
          {previewVideo && (
            <div>
              <div className="relative bg-black">
                <video
                  className="w-full max-h-[70vh]"
                  src={`/api/files/${encodeURIComponent(previewVideo.video)}`}
                  controls
                  autoPlay
                  controlsList="nodownload"
                />
              </div>
              <div className="p-4">
                <DialogHeader>
                  <DialogTitle className="text-sm">{previewVideo.job_id}</DialogTitle>
                  <DialogDescription className="text-xs">{previewVideo.video}</DialogDescription>
                </DialogHeader>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
