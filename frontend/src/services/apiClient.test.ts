import { describe, expect, it, vi } from 'vitest'
import { ApiClient, ApiError } from './apiClient'

describe('ApiClient', () => {
  it('returns typed data from the existing response envelope', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 0, data: { I18n: 'zh-CN' } }),
    })
    const data = await new ApiClient('/api', fetcher).getSaveConfig()
    expect(data.I18n).toBe('zh-CN')
  })

  it('normalizes network failures into an API error', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('offline'))
    await expect(new ApiClient('/api', fetcher).getSaveConfig()).rejects.toEqual(
      new ApiError('Backend is unavailable.', 0),
    )
  })
})
