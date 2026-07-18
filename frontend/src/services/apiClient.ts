export interface ApiEnvelope<T> {
  status: number
  data?: T
  msg?: string
}

export interface SaveConfigResponse {
  I18n: string
  I18nList: Record<string, string>
  Path: string | null
  HasPassword: boolean
  VERSION: string
  IsOfficialBuild: boolean
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
  }
}

export class ApiClient {
  constructor(
    private readonly baseUrl = '/api',
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  async getSaveConfig(): Promise<SaveConfigResponse> {
    return this.request<SaveConfigResponse>('/save/fetch_config')
  }

  async loadSave(readPath: string, token: string): Promise<void> {
    await this.request('/save/load', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ ReadPath: readPath }),
    })
  }

  async saveTo(writePath: string, token: string): Promise<void> {
    await this.request('/save/save', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ WritePath: writePath }),
    })
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await this.fetcher(`${this.baseUrl}${path}`, init)
    } catch {
      throw new ApiError('Backend is unavailable.', 0)
    }
    const payload = (await response.json()) as ApiEnvelope<T>
    if (!response.ok || payload.status !== 0) {
      throw new ApiError(payload.msg || 'The request failed.', response.status)
    }
    return payload.data as T
  }
}
