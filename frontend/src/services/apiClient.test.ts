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
      new ApiError('Backend is unavailable.', 0, 0),
    )
  })

  it('attaches the session token to authenticated requests', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ status: 0, data: { access_token: 'token-1' } }) })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ status: 0, data: { Loaded: false } }) })
    const client = new ApiClient('/api', fetcher)
    await client.login('')
    await client.getSession()
    const headers = fetcher.mock.calls[1][1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer token-1')
  })

  it('preserves the response-envelope error message', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ status: 1, data: null, msg: 'Palbox is full.' }),
    })
    await expect(new ApiClient('/api', fetcher).getSession()).rejects.toMatchObject({
      message: 'Palbox is full.', httpStatus: 409, apiStatus: 1,
    })
  })

  it('sends item moves through the typed player-scoped endpoint', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 0, data: { Inventory: {}, DirtyRevision: 3 } }),
    })
    const client = new ApiClient('/api', fetcher)
    await client.moveItem(
      'player/one',
      { Container: 'common', SlotIndex: 2 },
      { Container: 'weapon', SlotIndex: 0 },
    )
    expect(fetcher).toHaveBeenCalledWith(
      '/api/item/player/player%2Fone/move',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetcher.mock.calls[0][1].body).toContain('"SlotIndex":2')
  })

  it('sends the explicit save kind and dedicated stop confirmation', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 0, data: {} }),
    })
    const client = new ApiClient('/api', fetcher)
    await client.loadSave('D:\\WorldId', 'dedicated')
    await client.commitDraft(true)

    expect(fetcher.mock.calls[0][1].body).toBe(
      JSON.stringify({ ReadPath: 'D:\\WorldId', SaveKind: 'dedicated' }),
    )
    expect(fetcher.mock.calls[1][1].body).toBe(
      JSON.stringify({ ServerStoppedConfirmed: true }),
    )
  })
})
