import { defineStore } from 'pinia'
import { apiClient } from '@/services/apiClient'
import type { PalDetail, PalFilters, PalSummary, PlayerDetail, PlayerSummary } from '@/types/domain'
import { useDraftStore } from './draft'
import { useSessionStore } from './session'

function summaryFromDetail(pal: PalDetail): PalSummary {
  const {
    InstanceId, CharacterID, SpeciesKey, SpeciesName, NickName, IconAccessKey, PalDeckId,
    Level, Gender, OwnerPlayerUId, OwnerName, ObjectType, Location, Elements, StateFlags, IsAnomalous,
  } = pal
  return {
    InstanceId, CharacterID, SpeciesKey, SpeciesName, NickName, IconAccessKey, PalDeckId,
    Level, Gender, OwnerPlayerUId, OwnerName, ObjectType, Location, Elements, StateFlags, IsAnomalous,
  }
}

export const useCollectionStore = defineStore('collection', {
  state: () => ({
    pals: [] as PalSummary[],
    selectedPal: null as PalDetail | null,
    players: [] as PlayerSummary[],
    selectedPlayer: null as PlayerDetail | null,
    loading: false,
    error: '',
    filters: {
      query: '', owner: '', location: '', element: '', objectType: '', anomaly: '', sort: 'deck',
    } as PalFilters,
  }),
  getters: {
    filteredPals(state): PalSummary[] {
      const query = state.filters.query.trim().toLocaleLowerCase()
      const items = state.pals.filter((pal) => {
        const searchable = `${pal.SpeciesName} ${pal.NickName} ${pal.CharacterID} ${pal.InstanceId} ${pal.OwnerName || ''}`.toLocaleLowerCase()
        return (!query || searchable.includes(query))
          && (!state.filters.owner || pal.OwnerPlayerUId === state.filters.owner)
          && (!state.filters.location || pal.Location === state.filters.location)
          && (!state.filters.element || pal.Elements.includes(state.filters.element))
          && (!state.filters.objectType || pal.ObjectType === state.filters.objectType)
          && (!state.filters.anomaly || (state.filters.anomaly === 'yes' ? pal.IsAnomalous : !pal.IsAnomalous))
      })
      return items.sort((a, b) => {
        switch (state.filters.sort) {
          case 'level': return b.Level - a.Level || a.SpeciesName.localeCompare(b.SpeciesName)
          case 'name': return a.SpeciesName.localeCompare(b.SpeciesName) || a.NickName.localeCompare(b.NickName)
          case 'owner': return (a.OwnerName || '').localeCompare(b.OwnerName || '') || a.SpeciesName.localeCompare(b.SpeciesName)
          default: return (a.PalDeckId || '9999').localeCompare(b.PalDeckId || '9999', undefined, { numeric: true }) || a.SpeciesName.localeCompare(b.SpeciesName)
        }
      })
    },
  },
  actions: {
    async loadPals(force = false) {
      if (this.pals.length && !force) return
      this.loading = true
      try {
        this.pals = await apiClient.listPals()
        this.syncSessionStatistics()
      } finally {
        this.loading = false
      }
    },
    async loadPlayers(force = false) {
      if (this.players.length && !force) return
      this.players = await apiClient.listPlayers()
      this.syncSessionStatistics()
    },
    async loadPal(instanceId: string) {
      this.loading = true
      try {
        this.selectedPal = await apiClient.getPal(instanceId)
        return this.selectedPal
      } finally {
        this.loading = false
      }
    },
    async patchPal(instanceId: string, changes: Partial<PalDetail>) {
      const result = await useDraftStore().runMutation(() => apiClient.patchPal(instanceId, changes))
      this.selectedPal = result.Pal
      this.upsertPal(summaryFromDetail(result.Pal))
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      return result.Pal
    },
    async createPal(ownerPlayerUId: string, characterId: string) {
      const result = await useDraftStore().runMutation(() => apiClient.createPal(ownerPlayerUId, characterId))
      this.upsertPal(summaryFromDetail(result.Pal))
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      return result.Pal
    },
    async duplicatePal(instanceId: string) {
      const result = await useDraftStore().runMutation(() => apiClient.duplicatePal(instanceId))
      this.upsertPal(summaryFromDetail(result.Pal))
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      return result.Pal
    },
    async deletePal(instanceId: string) {
      const result = await useDraftStore().runMutation(() => apiClient.deletePal(instanceId))
      this.pals = this.pals.filter((pal) => pal.InstanceId !== instanceId)
      if (this.selectedPal?.InstanceId === instanceId) this.selectedPal = null
      this.syncSessionStatistics()
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
    },
    async retrievePal(instanceId: string) {
      const result = await useDraftStore().runMutation(() => apiClient.retrievePal(instanceId))
      this.selectedPal = result.Pal
      this.upsertPal(summaryFromDetail(result.Pal))
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
    },
    async healAll() {
      const result = await useDraftStore().runMutation(() => apiClient.healAllPals())
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      await this.loadPals(true)
      return result.Healed
    },
    async loadPlayer(playerId: string) {
      this.selectedPlayer = await apiClient.getPlayer(playerId)
      return this.selectedPlayer
    },
    async patchPlayer(playerId: string, changes: Partial<PlayerDetail>) {
      const result = await useDraftStore().runMutation(() => apiClient.patchPlayer(playerId, changes))
      this.selectedPlayer = result.Player
      this.upsertPlayer(result.Player)
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      return result.Player
    },
    async patchTechnology(playerId: string, technologyId: string, enabled: boolean) {
      const result = await useDraftStore().runMutation(() => apiClient.patchTechnology(playerId, technologyId, enabled))
      if (this.selectedPlayer?.PlayerUId === playerId) {
        const values = new Set(this.selectedPlayer.UnlockedRecipeTechnologyNames)
        enabled ? values.add(technologyId) : values.delete(technologyId)
        this.selectedPlayer.UnlockedRecipeTechnologyNames = [...values]
      }
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
    },
    async unlockAllTechnology(playerId: string) {
      const result = await useDraftStore().runMutation(() => apiClient.unlockAllTechnology(playerId))
      this.selectedPlayer = result.Player
      this.upsertPlayer(result.Player)
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
    },
    upsertPal(pal: PalSummary) {
      const index = this.pals.findIndex((item) => item.InstanceId === pal.InstanceId)
      if (index === -1) this.pals.push(pal)
      else this.pals[index] = pal
      this.syncSessionStatistics()
    },
    upsertPlayer(player: PlayerSummary) {
      const index = this.players.findIndex((item) => item.PlayerUId === player.PlayerUId)
      if (index === -1) this.players.push(player)
      else this.players[index] = player
      this.syncSessionStatistics()
    },
    syncSessionStatistics() {
      const session = useSessionStore()
      const humans = this.pals.filter((pal) => pal.ObjectType === 'human').length
      session.session.Statistics = {
        Players: this.players.length || session.session.Statistics.Players,
        Pals: this.pals.length - humans,
        Humans: humans,
        Anomalies: this.pals.filter((pal) => pal.IsAnomalous).length,
        Objects: this.pals.length,
      }
    },
    clear() {
      this.pals = []
      this.players = []
      this.selectedPal = null
      this.selectedPlayer = null
    },
  },
})
