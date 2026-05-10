import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  FileText,
  Video,
  ListTodo,
  Settings,
  PenLine,
} from 'lucide-react'

const navItems = [
  { to: '/', label: '总览', icon: LayoutDashboard },
  { to: '/scripts', label: '文案', icon: FileText },
  { to: '/produce', label: '制作', icon: Video },
  { to: '/jobs', label: '任务', icon: ListTodo },
  { to: '/videos', label: '视频库', icon: Video },
  { to: '/tweets', label: '推文库', icon: PenLine },
  { to: '/settings', label: '设置', icon: Settings },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-bold">
            AI
          </div>
          <span>内容生产</span>
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const active = location.pathname === item.to ||
              (item.to !== '/' && location.pathname.startsWith(item.to))
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? 'text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
                {active && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute inset-0 rounded-lg bg-accent -z-10"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
