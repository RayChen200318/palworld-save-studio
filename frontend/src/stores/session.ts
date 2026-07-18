import { defineStore } from 'pinia'
import { apiClient } from '@/services/apiClient'
import type { Locale, SaveConfig, SaveSession } from '@/types/domain'

let bootstrapRequest: Promise<void> | null = null

const emptySession = (): SaveSession => ({
  Path: null,
  Loaded: false,
  DirtyRevision: 0,
  Dirty: false,
  Statistics: { Players: 0, Pals: 0, Humans: 0, Anomalies: 0, Objects: 0 },
  BackupEnabled: true,
  BackupPath: null,
  LastCommit: null,
})

export const useSessionStore = defineStore('session', {
  state: () => ({
    locale: 'zh-CN' as Locale,
    config: null as SaveConfig | null,
    session: emptySession(),
    initialized: false,
    busy: false,
    error: '',
  }),
  getters: {
    loaded: (state) => state.session.Loaded,
    dirty: (state) => state.session.Dirty,
    worldName: (state) => {
      const path = state.session.Path
      if (!path) return ''
      return path.split(/[\\/]/).filter(Boolean).at(-1) || path
    },
  },
  actions: {
    async bootstrap() {
      if (this.initialized) return
      if (bootstrapRequest) {
        await bootstrapRequest
        return
      }
      bootstrapRequest = (async () => {
        this.busy = true
        this.error = ''
        try {
          this.config = await apiClient.getSaveConfig()
          this.locale = this.config.I18n === 'en' ? 'en' : 'zh-CN'
          document.documentElement.lang = this.locale
          await apiClient.login('')
          this.session = await apiClient.getSession()
          this.initialized = true
        } catch (error) {
          this.error = error instanceof Error ? error.message : String(error)
        } finally {
          this.busy = false
        }
      })()
      try {
        await bootstrapRequest
      } finally {
        bootstrapRequest = null
      }
    },
    async setLocale(locale: Locale) {
      this.locale = locale
      document.documentElement.lang = locale
      await apiClient.updateLocale(locale)
    },
    async toggleLocale() {
      await this.setLocale(this.locale === 'zh-CN' ? 'en' : 'zh-CN')
    },
    async loadSave(path: string) {
      this.busy = true
      this.error = ''
      try {
        this.session = await apiClient.loadSave(path)
        return true
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        return false
      } finally {
        this.busy = false
      }
    },
    async discardDraft() {
      this.busy = true
      try {
        this.session = await apiClient.discardDraft()
      } finally {
        this.busy = false
      }
    },
    async commitDraft() {
      this.busy = true
      this.error = ''
      try {
        const result = await apiClient.commitDraft()
        this.session = result.Session
        return result.Commit
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        throw error
      } finally {
        this.busy = false
      }
    },
    async setBackupEnabled(enabled: boolean) {
      this.session = await apiClient.updateBackupSetting(enabled)
    },
    applyDirtyRevision(revision: number) {
      this.session.DirtyRevision = revision
      this.session.Dirty = revision > 0
    },
    replaceSession(session: SaveSession) {
      this.session = session
    },
  },
})
