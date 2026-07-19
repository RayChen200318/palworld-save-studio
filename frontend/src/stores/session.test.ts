import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/apiClient'
import type { SaveConfig, SaveSession } from '@/types/domain'
import { useSessionStore } from './session'

const config: SaveConfig = {
  I18n: 'zh-CN',
  I18nList: { 'zh-CN': '简体中文', en: 'English' },
  Path: null,
  HasPassword: false,
  VERSION: '0.4.0',
  IsOfficialBuild: false,
  BackupEnabled: true,
}

const session: SaveSession = {
  Path: null,
  Loaded: false,
  DirtyRevision: 0,
  Dirty: false,
  Statistics: { Players: 0, Pals: 0, Humans: 0, Anomalies: 0, Objects: 0 },
  BackupEnabled: true,
  BackupPath: null,
  LastCommit: null,
}

describe('session bootstrap', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('coalesces concurrent initialization into one request chain', async () => {
    const getConfig = vi.spyOn(apiClient, 'getSaveConfig').mockResolvedValue(config)
    const login = vi.spyOn(apiClient, 'login').mockResolvedValue('token')
    const getSession = vi.spyOn(apiClient, 'getSession').mockResolvedValue(session)
    const store = useSessionStore()

    await Promise.all([store.bootstrap(), store.bootstrap(), store.bootstrap()])

    expect(getConfig).toHaveBeenCalledOnce()
    expect(login).toHaveBeenCalledOnce()
    expect(getSession).toHaveBeenCalledOnce()
    expect(store.initialized).toBe(true)
  })
})
