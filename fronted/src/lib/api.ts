const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(body.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // 文案
  generate: (topic: string, style?: string) =>
    request<{ script: string }>('/generate', {
      method: 'POST',
      body: JSON.stringify({ topic, style }),
    }),

  polish: (input: string, feedback: string) =>
    request<{ status: string; message: string }>('/polish', {
      method: 'POST',
      body: JSON.stringify({ input, feedback }),
    }),

  // 系统
  status: () =>
    request<{ collection: string; doc_count: number; instances: string[] }>('/status'),

  // 任务
  listJobs: (status?: string) =>
    request<any[]>(`/jobs${status ? `?status=${status}` : ''}`),

  getJob: (id: string) =>
    request<any>(`/jobs/${id}`),

  cancelJob: (id: string) =>
    request<{ status: string; message: string }>(`/jobs/${id}/cancel`, {
      method: 'POST',
    }),

  // 文件
  listScripts: () =>
    request<{ name: string; path: string; size: number; modified: number }[]>('/scripts'),

  saveScript: (path: string, content: string) =>
    request<{ status: string; name: string; path: string; size: number }>('/scripts', {
      method: 'PUT',
      body: JSON.stringify({ path, content }),
    }),

  listVideos: () =>
    request<{ job_id: string; path: string; videos: string[] }[]>('/videos'),

  listTweets: () =>
    request<{ name: string; path: string; article: string; article_raw: string; images: string[]; created_at: number }[]>('/tweets'),

  saveTweet: (path: string, content: string) =>
    request<{ status: string; name: string; path: string; size: number }>('/tweets', {
      method: 'PUT',
      body: JSON.stringify({ path, content }),
    }),

  // 视频生产
  produceSeedance: (params: Record<string, any>) =>
    request<{ job_id: string }>('/produce-seedance', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  produce: (params: Record<string, any>) =>
    request<{ job_id: string }>('/produce', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  produceRemotion: (params: Record<string, any>) =>
    request<{ job_id: string }>('/produce-remotion', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  produceHyperframes: (params: Record<string, any>) =>
    request<{ job_id: string }>('/produce-hyperframes', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // 图文推文
  generateTweet: (params: Record<string, any>) =>
    request<{ job_id: string }>('/generate-tweet', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // 摄入
  ingest: (file: File, force?: boolean) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE_URL}/ingest?force=${force ?? false}`, {
      method: 'POST',
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({ error: res.statusText }))
        throw new Error(body.error || `HTTP ${res.status}`)
      }
      return res.json() as Promise<{ job_id: string }>
    })
  },

  ingestText: (text: string, name?: string, force?: boolean) =>
    request<{ status: string; message: string }>('/ingest-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, name, force }),
    }),
}
