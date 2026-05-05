import { Link } from 'react-router-dom'

const features = [
  {
    title: '文案生成',
    desc: '根据话题自动生成短视频文案，支持知识库检索增强',
    to: '/scripts',
    icon: ' ',
  },
  {
    title: '视频制作',
    desc: '文案 → 分镜 → 图片 → 动画 → 视频，全链路自动化',
    to: '/videos',
    icon: ' ',
  },
  {
    title: '任务管理',
    desc: '查看异步任务状态，跟踪视频生成进度',
    to: '/jobs',
    icon: '⚙️',
  },
]

export default function Home() {
  return (
    <div>
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">AI 内容生产系统</h1>
        <p className="mt-2 text-gray-500">短视频文案自动生成 & 视频制作</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <Link
            key={f.to}
            to={f.to}
            className="group rounded-xl border border-gray-200 bg-white p-6 transition-all hover:border-gray-300 hover:shadow-md"
          >
            <div className="mb-3 text-3xl">{f.icon}</div>
            <h2 className="mb-1 text-lg font-semibold text-gray-900 group-hover:text-blue-600">
              {f.title}
            </h2>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
