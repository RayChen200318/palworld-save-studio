import { defineStore } from 'pinia'
import type { Locale } from '@/types/domain'

export const usePrototypeStore = defineStore('prototype', {
  state: () => ({
    locale: 'zh-CN' as Locale,
    saveLoaded: false,
    dirty: false,
    lastSavedAt: '' as string,
  }),
  actions: {
    toggleLocale() {
      this.locale = this.locale === 'zh-CN' ? 'en' : 'zh-CN'
      document.documentElement.lang = this.locale
    },
    openMockSave() {
      this.saveLoaded = true
      this.dirty = false
    },
    markDirty() {
      this.dirty = true
    },
    saveDraft() {
      this.dirty = false
      this.lastSavedAt = new Date().toISOString()
    },
    discardDraft() {
      this.dirty = false
    },
  },
})
