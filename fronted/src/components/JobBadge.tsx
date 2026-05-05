import { motion, AnimatePresence } from 'framer-motion'
import { Badge } from '@/components/ui/badge'

const statusConfig = {
  pending: { label: '等待中', variant: 'secondary' as const, color: 'bg-gray-400' },
  running: { label: '运行中', variant: 'default' as const, color: 'bg-blue-500' },
  success: { label: '成功', variant: 'default' as const, color: 'bg-green-500' },
  failed: { label: '失败', variant: 'destructive' as const, color: 'bg-red-500' },
  cancelled: { label: '已取消', variant: 'outline' as const, color: 'bg-orange-500' },
}

export function JobBadge({ status }: { status: string }) {
  const config = statusConfig[status as keyof typeof statusConfig] ?? statusConfig.pending

  return (
    <Badge variant={config.variant} className="gap-1.5">
      <AnimatePresence mode="wait">
        <motion.span
          key={status}
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.5, opacity: 0 }}
          transition={{ duration: 0.15 }}
          className={`inline-block h-2 w-2 rounded-full ${config.color} ${
            status === 'running' ? 'animate-pulse' : ''
          }`}
        />
      </AnimatePresence>
      {config.label}
    </Badge>
  )
}
