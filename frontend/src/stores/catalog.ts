import { defineStore } from 'pinia'
import { apiClient } from '@/services/apiClient'
import type { ActiveSkill, PalCatalogItem, PassiveSkill, TechnologyItem } from '@/types/domain'

export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    pals: [] as PalCatalogItem[],
    passives: [] as PassiveSkill[],
    actives: [] as ActiveSkill[],
    technologies: [] as TechnologyItem[],
    loaded: false,
    loading: false,
    error: '',
  }),
  getters: {
    palById: (state) => new Map(state.pals.map((pal) => [pal.InternalName, pal])),
    passiveById: (state) => new Map(state.passives.map((skill) => [skill.InternalName, skill])),
    activeById: (state) => new Map(state.actives.map((skill) => [skill.InternalName, skill])),
  },
  actions: {
    async load() {
      if (this.loaded || this.loading) return
      this.loading = true
      this.error = ''
      try {
        const result = await apiClient.getCatalog()
        this.pals = result.pals
        this.passives = result.passives
        this.actives = result.actives
        this.technologies = result.technologies.sort((a, b) => a.Level - b.Level || a.I18n.localeCompare(b.I18n))
        this.loaded = true
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
