import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import MainLayout from '@/layouts/MainLayout'
import Dashboard from '@/pages/Dashboard'
import Scripts from '@/pages/Scripts'
import Produce from '@/pages/Produce'
import Jobs from '@/pages/Jobs'
import Videos from '@/pages/Videos'
import Tweets from '@/pages/Tweets'
import Settings from '@/pages/Settings'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scripts" element={<Scripts />} />
            <Route path="/produce" element={<Produce />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/tweets" element={<Tweets />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
