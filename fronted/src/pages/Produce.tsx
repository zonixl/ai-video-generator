import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, Check, FileText, Settings2, ImageIcon, Film, Download, Eye, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { JobBadge } from '@/components/JobBadge'
import { useJob } from '@/hooks/useJob'
import { useJobs } from '@/hooks/useJobs'
import { useScripts } from '@/hooks/useScripts'
import { api } from '@/lib/api'
import { toast } from 'sonner'

const steps = [
  { label: '选择文案', icon: FileText },
  { label: '配置参数', icon: Settings2 },
  { label: '生成中', icon: Film },
  { label: '完成', icon: Check },
]

type EngineType = 'seedance' | 'remotion' | 'tweet'

const engineSteps: Record<EngineType, { value: string; label: string; desc: string }[]> = {
  seedance: [
    { value: 'all', label: '全部执行', desc: '从计划到最终合成' },
    { value: 'plan', label: '计划', desc: '生成分镜计划' },
    { value: 'images', label: '图片', desc: '生成场景图片' },
    { value: 'videos', label: '视频', desc: '图生视频片段' },
    { value: 'subtitles', label: '字幕', desc: '生成字幕文件' },
    { value: 'compose', label: '合成', desc: '合成最终视频' },
    { value: 'unify', label: '统一', desc: '统一尺寸/格式' },
  ],
  remotion: [
    { value: 'all', label: '全部执行', desc: '从计划到最终渲染' },
    { value: 'plan', label: '计划', desc: '生成分镜计划' },
    { value: 'tts', label: 'TTS 配音', desc: '生成语音文件' },
    { value: 'kinetic', label: '动态文字', desc: '生成动态文字排版' },
    { value: 'image', label: '图片', desc: '生成场景图片' },
    { value: 'refine', label: '精修', desc: '视觉自迭代优化' },
    { value: 'render', label: '渲染', desc: '渲染最终视频' },
  ],
  tweet: [
    { value: 'all', label: '一键生成', desc: '润色 + 插图 + 排版，一键完成' },
  ],
}

const sizePresets = [
  { label: '竖屏 9:16', w: 1080, h: 1920 },
  { label: '横屏 16:9', w: 1920, h: 1080 },
  { label: '方形 1:1', w: 1080, h: 1080 },
]

const remotionTemplates = [
  { value: '', label: '自动选择', desc: '由 AI 根据文案内容自动选择' },
  { value: 'basic_diagram', label: '图示卡片', desc: '卡片、箭头、指标、图表等组件入场动画，适合数据/流程/对比类' },
  { value: 'kinetic_text', label: '灵动文字', desc: '文字逐词弹出、上浮、翻转，配合语音节奏，适合金句/观点/短文案' },
  { value: 'image_full', label: '全屏背景图', desc: 'AI 生成图片铺满屏幕，标题居中叠加，适合风景/故事/宏大主题' },
  { value: 'image_elegant', label: '雅致插画', desc: '暖色背景+渐变光晕，上方圆角插画，下方排版文字，适合人文/哲理/情感类' },
  { value: 'image_card', label: '信息卡片', desc: '背景渐变+几何装饰，中央卡片含插画，适合科普/知识/解读类' },
  { value: 'image_modern', label: '现代科技', desc: '深色背景+几何线条，玻璃卡片内插画，适合科技/商业/趋势类' },
  { value: 'image_neon', label: '霓虹赛博', desc: '暗色底+霓虹渐变，粗体大字+荧光高亮，适合潮流/游戏/年轻化内容' },
]

export default function Produce() {
  const [step, setStep] = useState(0)
  const [engine, setEngine] = useState<EngineType>('seedance')
  const [scriptPath, setScriptPath] = useState('')
  const [title, setTitle] = useState('')
  const [output, setOutput] = useState('')
  const [audioMode, setAudioMode] = useState('tts')
  const [pipelineStep, setPipelineStep] = useState('all')
  const [resumeJobId, setResumeJobId] = useState('')
  const [resumeMode, setResumeMode] = useState<'select' | 'manual'>('select')
  const [force, setForce] = useState(false)
  const [jobId, setJobId] = useState('')

  // 尺寸 & 帧率
  const [width, setWidth] = useState<number | ''>('')
  const [height, setHeight] = useState<number | ''>('')
  const [fps, setFps] = useState<number | ''>('')

  // Seedance 专属
  const [regenerate, setRegenerate] = useState<number | ''>('')
  const [userImages, setUserImages] = useState('')

  // Remotion 专属
  const [orientation, setOrientation] = useState('')
  const [kinetic, setKinetic] = useState(false)
  const [template, setTemplate] = useState('')
  const [refine, setRefine] = useState(false)
  const [refineRounds, setRefineRounds] = useState<number | ''>('')
  const [reviewOnly, setReviewOnly] = useState(false)
  const [ttsMode, setTtsMode] = useState('per_scene')

  // Tweet 专属
  const [tweetTopic, setTweetTopic] = useState('')
  const [tweetDraft, setTweetDraft] = useState('')
  const [tweetFeedback, setTweetFeedback] = useState('')
  const [tweetNoImages, setTweetNoImages] = useState(false)

  const { data: scripts } = useScripts()
  const { data: job } = useJob(jobId)
  const { data: allJobs } = useJobs()
  const recentJobs = (allJobs ?? []).filter(
    (j) => j.status === 'success' || j.status === 'failed' || j.status === 'cancelled'
  ).slice(0, 20)

  // 文案预览
  const [previewFile, setPreviewFile] = useState<{ name: string; path: string } | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)

  const handlePreview = async (file: { name: string; path: string }, e: React.MouseEvent) => {
    e.stopPropagation()
    setPreviewFile(file)
    setPreviewContent('')
    setPreviewLoading(true)
    try {
      const res = await fetch(`/api/files/${encodeURIComponent(file.path)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const text = await res.text()
      setPreviewContent(text)
    } catch (err) {
      setPreviewContent(`加载失败: ${(err as Error).message}`)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleStart = async () => {
    try {
      // Tweet 模式：独立逻辑
      if (engine === 'tweet') {
        if (!tweetTopic && !tweetDraft) {
          toast.error('请输入话题或提供初稿路径')
          return
        }
        const params: Record<string, any> = {}
        if (tweetTopic) params.topic = tweetTopic
        if (tweetDraft && tweetDraft !== 'draft') params.draft_path = tweetDraft
        if (tweetFeedback) params.feedback = tweetFeedback
        if (output) params.output = output
        params.no_images = tweetNoImages

        const res = await api.generateTweet(params)
        setJobId(res.job_id)
        setStep(2)
        toast.success('推文任务已提交')
        return
      }

      // 视频模式
      if (!scriptPath) {
        toast.error('请选择文案文件')
        return
      }
      const params: Record<string, any> = {
        script: scriptPath,
        title: title || undefined,
        output: output || undefined,
        width: width || undefined,
        height: height || undefined,
        fps: fps || undefined,
        step: pipelineStep,
        force,
      }

      if (resumeJobId.trim()) {
        params.job_id = resumeJobId.trim()
      }

      if (engine === 'seedance') {
        params.audio_mode = audioMode
        params.use_tts = audioMode === 'tts'
        params.auto_confirm = true
        if (regenerate) params.regenerate = regenerate
        if (userImages.trim()) params.user_images = userImages.trim()
      } else {
        params.use_tts = audioMode === 'tts'
        if (audioMode === 'tts') params.tts_mode = ttsMode
        if (orientation) params.orientation = orientation
        params.kinetic = kinetic
        if (template) params.template = template
        params.refine = refine
        if (refineRounds) params.refine_rounds = refineRounds
        params.review_only = reviewOnly
      }

      let res
      if (engine === 'seedance') {
        res = await api.produceSeedance(params)
      } else {
        res = await api.produceRemotion(params)
      }
      setJobId(res.job_id)
      setStep(2)
      toast.success('任务已提交')
    } catch (e) {
      toast.error(`提交失败: ${(e as Error).message}`)
    }
  }

  const isRunning = job?.status === 'running' || job?.status === 'pending'
  const isSuccess = job?.status === 'success'
  const isFailed = job?.status === 'failed'
  const isCancelled = job?.status === 'cancelled'

  if ((isSuccess || isFailed || isCancelled) && step === 2) {
    if (isSuccess) setStep(3)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {engine === 'tweet' ? '图文推文' : '视频制作'}
        </h1>
        <p className="mt-1 text-muted-foreground">
          {engine === 'tweet' ? '话题/初稿 → 知识库润色 → 插图 → 排版输出' : '向导式视频生产流程'}
        </p>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center gap-2">
        {steps.map((s, i) => {
          const Icon = s.icon
          const active = i === step
          const done = i < step
          return (
            <div key={s.label} className="flex items-center gap-2">
              <motion.div
                className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  done
                    ? 'bg-primary text-primary-foreground'
                    : active
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-muted text-muted-foreground'
                }`}
                animate={{ scale: active ? 1.05 : 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              >
                <Icon className="h-4 w-4" />
                {s.label}
              </motion.div>
              {i < steps.length - 1 && (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          )
        })}
      </div>

      {/* 步骤内容 */}
      <AnimatePresence mode="wait">
        {step === 0 && (
          <motion.div
            key="step0"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>选择文案文件</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {(scripts ?? []).map((s) => (
                    <motion.div
                      key={s.path}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card
                        className={`cursor-pointer transition-all ${
                          scriptPath === s.path
                            ? 'ring-2 ring-primary'
                            : 'hover:shadow-md'
                        }`}
                        onClick={() => setScriptPath(s.path)}
                      >
                        <CardContent className="flex items-center gap-3 p-4">
                          <FileText className="h-5 w-5 text-muted-foreground" />
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-medium">{s.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {(s.size / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            className="h-7 w-7 shrink-0"
                            onClick={(e) => handlePreview(s, e)}
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          {scriptPath === s.path && (
                            <Check className="h-4 w-4 text-primary" />
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <Input
                    placeholder="或直接输入文案文件路径"
                    value={scriptPath}
                    onChange={(e) => setScriptPath(e.target.value)}
                    className="flex-1"
                  />
                </div>
                <Button onClick={() => setStep(1)} disabled={engine !== 'tweet' && !scriptPath}>
                  下一步
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>配置参数</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* ---- 基础信息 ---- */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">视频标题</label>
                    <Input
                      placeholder="可选，默认从文案标题提取"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">输出路径</label>
                    <Input
                      placeholder="可选，默认 outputs/videos/..."
                      value={output}
                      onChange={(e) => setOutput(e.target.value)}
                    />
                  </div>
                </div>

                {/* ---- 视频引擎 ---- */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">视频引擎</label>
                  <div className="flex gap-3">
                    {(['seedance', 'remotion', 'tweet'] as EngineType[]).map((e) => (
                      <motion.div key={e} whileTap={{ scale: 0.97 }}>
                        <Badge
                          variant={engine === e ? 'default' : 'outline'}
                          className="cursor-pointer px-4 py-2 text-sm"
                          onClick={() => {
                            setEngine(e)
                            setPipelineStep('all')
                          }}
                        >
                          {e === 'seedance' ? 'Seedance 图生视频' : e === 'remotion' ? 'Remotion 图示' : '图文推文'}
                        </Badge>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* ---- 尺寸 & 帧率 ---- */}
                <div className="space-y-3">
                  <label className="text-sm font-medium">尺寸 & 帧率</label>
                  <div className="flex gap-2 flex-wrap">
                    {sizePresets.map((p) => (
                      <Badge
                        key={p.label}
                        variant={width === p.w && height === p.h ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => { setWidth(p.w); setHeight(p.h) }}
                      >
                        {p.label}
                      </Badge>
                    ))}
                  </div>
                  <div className="grid gap-3 grid-cols-3">
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">宽度</label>
                      <Input
                        type="number"
                        placeholder="如 1080"
                        value={width}
                        onChange={(e) => setWidth(e.target.value ? parseInt(e.target.value) : '')}
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">高度</label>
                      <Input
                        type="number"
                        placeholder="如 1920"
                        value={height}
                        onChange={(e) => setHeight(e.target.value ? parseInt(e.target.value) : '')}
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">帧率 (fps)</label>
                      <Input
                        type="number"
                        placeholder="如 30"
                        value={fps}
                        onChange={(e) => setFps(e.target.value ? parseInt(e.target.value) : '')}
                      />
                    </div>
                  </div>
                </div>

                {/* ---- 音频模式 ---- */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">音频模式</label>
                  <div className="flex gap-3">
                    {[
                      { v: 'tts', label: 'TTS 配音' },
                      ...(engine === 'seedance' ? [{ v: 'seedance-audio', label: '自带音频' }] : []),
                      { v: 'none', label: '无音频' },
                    ].map((o) => (
                      <motion.div key={o.v} whileTap={{ scale: 0.97 }}>
                        <Badge
                          variant={audioMode === o.v ? 'default' : 'outline'}
                          className="cursor-pointer px-4 py-2 text-sm"
                          onClick={() => setAudioMode(o.v)}
                        >
                          {o.label}
                        </Badge>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* ---- TTS 合成模式（仅 Remotion + TTS 时显示） ---- */}
                {engine === 'remotion' && audioMode === 'tts' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">TTS 合成模式</label>
                    <div className="flex gap-3">
                      {[
                        { v: 'per_scene', label: '逐场景情绪', desc: '每段独立情绪，风格多变但可能不连贯' },
                        { v: 'whole_article', label: '整篇统一', desc: '全文统一风格，语调自然连贯' },
                      ].map((o) => (
                        <motion.div key={o.v} whileTap={{ scale: 0.97 }}>
                          <Badge
                            variant={ttsMode === o.v ? 'default' : 'outline'}
                            className="cursor-pointer px-4 py-2 text-sm"
                            onClick={() => setTtsMode(o.v)}
                          >
                            {o.label}
                          </Badge>
                        </motion.div>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {ttsMode === 'per_scene'
                        ? '每段文案独立选择情绪风格，适合内容差异大的视频'
                        : 'AI 分析全文基调后选择统一风格，语音更自然连贯'}
                    </p>
                  </div>
                )}

                {/* ---- Seedance 专属 ---- */}
                {engine === 'seedance' && (
                  <div className="space-y-3">
                    <label className="text-sm font-medium">Seedance 选项</label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">重生成场景编号</label>
                        <Input
                          type="number"
                          placeholder="留空不重生成"
                          value={regenerate}
                          onChange={(e) => setRegenerate(e.target.value ? parseInt(e.target.value) : '')}
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">自定义图片目录</label>
                        <Input
                          placeholder="留空使用 AI 生成"
                          value={userImages}
                          onChange={(e) => setUserImages(e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* ---- Remotion 专属 ---- */}
                {engine === 'remotion' && (
                  <div className="space-y-4">
                    <label className="text-sm font-medium">Remotion 选项</label>

                    {/* 预设画幅 */}
                    <div className="space-y-2">
                      <label className="text-xs text-muted-foreground">预设画幅（覆盖上面的宽高）</label>
                      <div className="flex gap-2">
                        {[
                          { v: '', label: '不使用' },
                          { v: 'portrait', label: '竖屏 9:16' },
                          { v: 'landscape', label: '横屏 16:9' },
                        ].map((o) => (
                          <Badge
                            key={o.v}
                            variant={orientation === o.v ? 'default' : 'outline'}
                            className="cursor-pointer px-3 py-1 text-xs"
                            onClick={() => setOrientation(o.v)}
                          >
                            {o.label}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* 模板 */}
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">模板</label>
                      <select
                        value={template}
                        onChange={(e) => setTemplate(e.target.value)}
                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      >
                        {remotionTemplates.map((t) => (
                          <option key={t.value} value={t.value}>
                            {t.label} — {t.desc}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 开关项 */}
                    <div className="flex gap-3 flex-wrap">
                      <Badge
                        variant={kinetic ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => setKinetic(!kinetic)}
                      >
                        {kinetic ? '动态文字：开启' : '动态文字：关闭'}
                      </Badge>
                      <Badge
                        variant={refine ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => setRefine(!refine)}
                      >
                        {refine ? '视觉自迭代：开启' : '视觉自迭代：关闭'}
                      </Badge>
                      <Badge
                        variant={reviewOnly ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => setReviewOnly(!reviewOnly)}
                      >
                        {reviewOnly ? '仅审查报告' : '正常输出'}
                      </Badge>
                    </div>

                    {/* 精修轮数 */}
                    {refine && (
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">最大精修轮数</label>
                        <Input
                          type="number"
                          placeholder="留空使用默认"
                          value={refineRounds}
                          onChange={(e) => setRefineRounds(e.target.value ? parseInt(e.target.value) : '')}
                          className="w-40"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* ---- 图文推文专属 ---- */}
                {engine === 'tweet' && (
                  <div className="space-y-4">
                    <label className="text-sm font-medium">图文推文选项</label>

                    {/* 输入方式 */}
                    <div className="space-y-2">
                      <label className="text-xs text-muted-foreground">输入方式</label>
                      <div className="flex gap-3">
                        <Badge
                          variant={!tweetDraft ? 'default' : 'outline'}
                          className="cursor-pointer px-4 py-2 text-sm"
                          onClick={() => { setTweetDraft(''); setTweetTopic('') }}
                        >
                          话题生成
                        </Badge>
                        <Badge
                          variant={tweetDraft ? 'default' : 'outline'}
                          className="cursor-pointer px-4 py-2 text-sm"
                          onClick={() => { setTweetTopic(''); setTweetDraft('draft') }}
                        >
                          初稿润色
                        </Badge>
                      </div>
                    </div>

                    {/* 话题输入 */}
                    {!tweetDraft && (
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">话题/关键词</label>
                        <Input
                          placeholder="如：为什么养成阅读习惯很重要"
                          value={tweetTopic}
                          onChange={(e) => setTweetTopic(e.target.value)}
                        />
                      </div>
                    )}

                    {/* 初稿路径 */}
                    {tweetDraft && (
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">初稿文件路径</label>
                        <Input
                          placeholder="如：outputs/scripts/xxx.md"
                          value={tweetDraft === 'draft' ? '' : tweetDraft}
                          onChange={(e) => setTweetDraft(e.target.value || 'draft')}
                        />
                      </div>
                    )}

                    {/* 润色意见 */}
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">润色意见（可选）</label>
                      <Input
                        placeholder="如：语气再轻松一点，多举例子"
                        value={tweetFeedback}
                        onChange={(e) => setTweetFeedback(e.target.value)}
                      />
                    </div>

                    {/* 选项开关 */}
                    <div className="flex gap-3">
                      <Badge
                        variant={tweetNoImages ? 'outline' : 'default'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => setTweetNoImages(!tweetNoImages)}
                      >
                        {tweetNoImages ? '不生成配图' : '生成配图'}
                      </Badge>
                    </div>
                  </div>
                )}

                {/* ---- 执行步骤 ---- */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">执行步骤</label>
                  <p className="text-xs text-muted-foreground">
                    选择从哪个步骤开始执行，可中断后从指定步骤重启
                  </p>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {engineSteps[engine].map((s) => (
                      <motion.div key={s.value} whileTap={{ scale: 0.97 }}>
                        <Card
                          className={`cursor-pointer transition-all ${
                            pipelineStep === s.value
                              ? 'ring-2 ring-primary'
                              : 'hover:shadow-sm'
                          }`}
                          onClick={() => setPipelineStep(s.value)}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-center gap-2">
                              {pipelineStep === s.value && (
                                <Check className="h-3 w-3 text-primary" />
                              )}
                              <span className="text-sm font-medium">{s.label}</span>
                            </div>
                            <p className="mt-0.5 text-xs text-muted-foreground">{s.desc}</p>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* ---- 从已有任务继续 ---- */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">从已有任务继续（可选）</label>
                  <div className="flex gap-2">
                    <div className="flex gap-1">
                      <Badge
                        variant={resumeMode === 'select' ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => { setResumeMode('select'); setResumeJobId('') }}
                      >
                        下拉选择
                      </Badge>
                      <Badge
                        variant={resumeMode === 'manual' ? 'default' : 'outline'}
                        className="cursor-pointer px-3 py-1 text-xs"
                        onClick={() => { setResumeMode('manual'); setResumeJobId('') }}
                      >
                        手动输入
                      </Badge>
                    </div>
                  </div>
                  {resumeMode === 'select' ? (
                    <select
                      value={resumeJobId}
                      onChange={(e) => setResumeJobId(e.target.value)}
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    >
                      <option value="">不复用，从头开始</option>
                      {recentJobs.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.id} — {j.type} — {new Date(j.created_at * 1000).toLocaleString('zh-CN')}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <Input
                      placeholder="输入 job_id，如 seedance-a1b2c3d4"
                      value={resumeJobId}
                      onChange={(e) => setResumeJobId(e.target.value)}
                    />
                  )}
                </div>

                {/* ---- 强制重做 ---- */}
                <div className="flex items-center gap-3">
                  <motion.div whileTap={{ scale: 0.97 }}>
                    <Badge
                      variant={force ? 'default' : 'outline'}
                      className="cursor-pointer px-4 py-2 text-sm"
                      onClick={() => setForce(!force)}
                    >
                      {force ? '强制重做：开启' : '强制重做：关闭'}
                    </Badge>
                  </motion.div>
                  <span className="text-xs text-muted-foreground">
                    跳过已有结果，重新生成
                  </span>
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep(0)}>
                    上一步
                  </Button>
                  <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                    <Button onClick={handleStart}>
                      {pipelineStep === 'all' ? '开始制作' : `从 "${engineSteps[engine].find(s => s.value === pipelineStep)?.label}" 开始`}
                    </Button>
                  </motion.div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {isRunning ? '生成中' : isFailed ? '执行失败' : isCancelled ? '已取消' : '生成中'}
                  {isRunning && (
                    <motion.span
                      className="inline-block h-3 w-3 rounded-full bg-blue-500"
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                    />
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <JobBadge status={job?.status ?? 'pending'} />
                  <span className="text-sm text-muted-foreground">{jobId}</span>
                </div>
                {isRunning && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <Progress value={33} className="h-2" />
                    <p className="mt-2 text-sm text-muted-foreground">
                      正在处理，请稍候...
                    </p>
                  </motion.div>
                )}
                {isFailed && (
                  <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                    {job?.error}
                  </div>
                )}
                {(isFailed || isCancelled) && (
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={() => { setStep(1); setJobId('') }}>
                      重新配置
                    </Button>
                    <Button
                      onClick={() => {
                        if (job?.params) {
                          setPipelineStep(job.params.step || 'all')
                          setResumeJobId(jobId)
                        }
                        setStep(1)
                        setJobId('')
                      }}
                    >
                      从断点重启
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, type: 'spring' }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <Check className="h-5 w-5" />
                  制作完成
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {job?.result?.video_path && (
                  <div className="flex items-center gap-3">
                    <ImageIcon className="h-5 w-5 text-muted-foreground" />
                    <span className="text-sm">{job.result.video_path}</span>
                  </div>
                )}
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => { setStep(0); setJobId(''); setResumeJobId('') }}>
                    再次制作
                  </Button>
                  {engine === 'tweet' && job?.result && (
                    <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                      <Button onClick={() => window.open(`/api/files/${job.result.output_path || job.result.video_path}`, '_blank')}>
                        <Download className="mr-2 h-4 w-4" />
                        下载推文
                      </Button>
                    </motion.div>
                  )}
                  {engine !== 'tweet' && job?.result?.video_path && (
                    <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                      <Button onClick={() => window.open(`/api/files/${job.result.video_path}`, '_blank')}>
                        <Download className="mr-2 h-4 w-4" />
                        下载视频
                      </Button>
                    </motion.div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 文案预览弹窗 */}
      <Dialog open={!!previewFile} onOpenChange={(open) => { if (!open) { setPreviewFile(null); setPreviewContent('') } }}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {previewFile?.name}
            </DialogTitle>
            <DialogDescription>文案内容预览</DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto min-h-0">
            {previewLoading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed bg-muted/50 rounded-lg p-4 max-h-[60vh] overflow-auto">
                {previewContent}
              </pre>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
