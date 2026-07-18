import type {
  ActiveSkill,
  CommitResult,
  ItemCatalog,
  ItemContainerName,
  ItemMutationResult,
  PalCatalogItem,
  PalDetail,
  PalSummary,
  PassiveSkill,
  PathContext,
  PlayerDetail,
  PlayerInventory,
  PlayerSummary,
  SaveConfig,
  SaveSession,
  TechnologyItem,
  UpdateStatus,
} from '@/types/domain'

export interface ApiEnvelope<T> {
  status: number
  data: T | null
  msg: string | null
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly httpStatus: number,
    public readonly apiStatus = 1,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface DictionaryArray<T> {
  dict: Record<string, T>
  arr: T[]
}

interface PalCatalogResponse {
  dict: Record<string, PalCatalogItem>
  arr: PalCatalogItem[]
}

interface TechnologyResponse {
  techLvDict: Record<string, TechnologyItem[]>
}

export class ApiClient {
  private token = ''

  constructor(
    private readonly baseUrl = '/api',
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  setToken(token: string) {
    this.token = token
  }

  async login(password = ''): Promise<string> {
    const response = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }, false)
    this.token = response.access_token
    return response.access_token
  }

  getSaveConfig(): Promise<SaveConfig> {
    return this.request<SaveConfig>('/save/fetch_config', undefined, false)
  }

  getSession(): Promise<SaveSession> {
    return this.request<SaveSession>('/save/session')
  }

  loadSave(readPath: string): Promise<SaveSession> {
    return this.request<SaveSession>('/save/load', {
      method: 'POST',
      body: JSON.stringify({ ReadPath: readPath }),
    })
  }

  discardDraft(): Promise<SaveSession> {
    return this.request<SaveSession>('/save/discard', { method: 'POST' })
  }

  commitDraft(): Promise<{ Commit: CommitResult; Session: SaveSession }> {
    return this.request('/save/commit', { method: 'POST' })
  }

  updateBackupSetting(enabled: boolean): Promise<SaveSession> {
    return this.request('/save/settings', {
      method: 'PATCH',
      body: JSON.stringify({ BackupEnabled: enabled }),
    })
  }

  getUpdateStatus(): Promise<UpdateStatus> {
    return this.request('/save/update')
  }

  updateLocale(locale: string): Promise<void> {
    return this.request('/save/i18n', {
      method: 'PATCH',
      body: JSON.stringify({ I18n: locale }),
    }, false)
  }

  getPathContext(): Promise<PathContext> {
    return this.request('/save/path')
  }

  browsePath(path: string): Promise<PathContext> {
    return this.request('/save/path', {
      method: 'POST',
      body: JSON.stringify({ path }),
    })
  }

  pathBack(): Promise<PathContext> {
    return this.request('/save/path', { method: 'PATCH' })
  }

  async getCatalog(): Promise<{
    pals: PalCatalogItem[]
    passives: PassiveSkill[]
    actives: ActiveSkill[]
    technologies: TechnologyItem[]
  }> {
    const [pals, passives, actives, technologies] = await Promise.all([
      this.request<PalCatalogResponse>('/save/pal_data'),
      this.request<DictionaryArray<PassiveSkill>>('/save/passive_skills'),
      this.request<DictionaryArray<ActiveSkill>>('/save/active_skills'),
      this.request<TechnologyResponse>('/save/tech_data'),
    ])
    return {
      pals: pals.arr,
      passives: passives.arr,
      actives: actives.arr.filter((skill) => !skill.Invalid),
      technologies: Object.values(technologies.techLvDict).flat(),
    }
  }

  listPals(): Promise<PalSummary[]> {
    return this.request('/pal/list')
  }

  getPal(instanceId: string): Promise<PalDetail> {
    return this.request(`/pal/${encodeURIComponent(instanceId)}`)
  }

  patchPal(instanceId: string, changes: Partial<PalDetail>): Promise<{ Pal: PalDetail; DirtyRevision: number }> {
    return this.request(`/pal/${encodeURIComponent(instanceId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ changes }),
    })
  }

  createPal(ownerPlayerUId: string, characterId: string): Promise<{ Pal: PalDetail; DirtyRevision: number }> {
    return this.request('/pal', {
      method: 'POST',
      body: JSON.stringify({ OwnerPlayerUId: ownerPlayerUId, CharacterID: characterId }),
    })
  }

  duplicatePal(instanceId: string): Promise<{ Pal: PalDetail; DirtyRevision: number }> {
    return this.request(`/pal/${encodeURIComponent(instanceId)}/duplicate`, { method: 'POST' })
  }

  deletePal(instanceId: string): Promise<{ DirtyRevision: number }> {
    return this.request(`/pal/${encodeURIComponent(instanceId)}`, { method: 'DELETE' })
  }

  retrievePal(instanceId: string): Promise<{ Pal: PalDetail; DirtyRevision: number }> {
    return this.request(`/pal/${encodeURIComponent(instanceId)}/retrieve`, { method: 'POST' })
  }

  healAllPals(): Promise<{ Healed: number; DirtyRevision: number }> {
    return this.request('/pal/heal-all', { method: 'POST' })
  }

  getRawPal(instanceId: string): Promise<string> {
    return this.request<{ Json: string }>(`/pal/${encodeURIComponent(instanceId)}/raw`).then((result) => result.Json)
  }

  listPlayers(): Promise<PlayerSummary[]> {
    return this.request('/player')
  }

  getPlayer(playerId: string): Promise<PlayerDetail> {
    return this.request(`/player/${encodeURIComponent(playerId)}`)
  }

  patchPlayer(playerId: string, changes: Partial<PlayerDetail>): Promise<{ Player: PlayerDetail; DirtyRevision: number }> {
    return this.request(`/player/${encodeURIComponent(playerId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ changes }),
    })
  }

  patchTechnology(playerId: string, technologyId: string, enabled: boolean): Promise<{ Technology: string; Enabled: boolean; DirtyRevision: number }> {
    return this.request(`/player/${encodeURIComponent(playerId)}/technology/${encodeURIComponent(technologyId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ Enabled: enabled }),
    })
  }

  unlockAllTechnology(playerId: string): Promise<{ Player: PlayerDetail; DirtyRevision: number }> {
    return this.request(`/player/${encodeURIComponent(playerId)}/technology/unlock-all`, { method: 'POST' })
  }

  getItemCatalog(): Promise<ItemCatalog> {
    return this.request('/item/catalog')
  }

  getPlayerInventory(playerId: string): Promise<PlayerInventory> {
    return this.request(`/item/player/${encodeURIComponent(playerId)}`)
  }

  createItem(
    playerId: string,
    payload: {
      StaticId: string
      Container: ItemContainerName
      Quantity?: number
      SlotIndex?: number
      EggCharacterId?: string
    },
  ): Promise<ItemMutationResult> {
    return this.request(`/item/player/${encodeURIComponent(playerId)}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  patchItem(
    playerId: string,
    container: ItemContainerName,
    slotIndex: number,
    changes: Record<string, number | string>,
  ): Promise<ItemMutationResult> {
    return this.request(`/item/player/${encodeURIComponent(playerId)}/${container}/${slotIndex}`, {
      method: 'PATCH',
      body: JSON.stringify({ changes }),
    })
  }

  deleteItem(
    playerId: string,
    container: ItemContainerName,
    slotIndex: number,
    confirmDangerous = false,
  ): Promise<ItemMutationResult> {
    return this.request(`/item/player/${encodeURIComponent(playerId)}/${container}/${slotIndex}`, {
      method: 'DELETE',
      body: JSON.stringify({ ConfirmDangerous: confirmDangerous }),
    })
  }

  moveItem(
    playerId: string,
    source: { Container: ItemContainerName; SlotIndex: number },
    target: { Container: ItemContainerName; SlotIndex: number },
  ): Promise<ItemMutationResult> {
    return this.request(`/item/player/${encodeURIComponent(playerId)}/move`, {
      method: 'POST',
      body: JSON.stringify({ Source: source, Target: target }),
    })
  }

  private async request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
    const headers = new Headers(init.headers)
    if (init.body) headers.set('Content-Type', 'application/json')
    if (authenticated && this.token) headers.set('Authorization', `Bearer ${this.token}`)

    let response: Response
    try {
      response = await this.fetcher.call(globalThis, `${this.baseUrl}${path}`, { ...init, headers })
    } catch {
      throw new ApiError('Backend is unavailable.', 0, 0)
    }

    let payload: ApiEnvelope<T>
    try {
      payload = (await response.json()) as ApiEnvelope<T>
    } catch {
      throw new ApiError('Backend returned an invalid response.', response.status, 1)
    }
    if (!response.ok || payload.status !== 0) {
      throw new ApiError(payload.msg || 'The request failed.', response.status, payload.status)
    }
    return payload.data as T
  }
}

export const apiClient = new ApiClient()
