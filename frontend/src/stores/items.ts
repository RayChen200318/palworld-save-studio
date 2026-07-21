import { defineStore } from 'pinia'
import { apiClient } from '@/services/apiClient'
import type {
  ItemCatalog,
  ItemCatalogEntry,
  ItemContainerName,
  ItemMutationResult,
  ItemSlot,
  PlayerInventory,
} from '@/types/domain'
import { useDraftStore } from './draft'
import { useSessionStore } from './session'

const containerOrder: ItemContainerName[] = ['common', 'essential', 'food', 'weapon', 'armor', 'drop']

export const useItemsStore = defineStore('items', {
  state: () => ({
    catalog: null as ItemCatalog | null,
    inventory: null as PlayerInventory | null,
    selectedPlayerId: '',
    selectedContainer: 'common' as ItemContainerName,
    selectedSlotIndex: null as number | null,
    query: '',
    category: '',
    rarity: '',
    loading: false,
    error: '',
  }),
  getters: {
    containerNames: () => containerOrder,
    activeContainer(state) {
      return state.inventory?.Containers[state.selectedContainer] || null
    },
    selectedSlot(state): ItemSlot | null {
      if (state.selectedSlotIndex === null || !state.inventory) return null
      return state.inventory.Containers[state.selectedContainer].Slots
        .find((slot) => slot.SlotIndex === state.selectedSlotIndex) || null
    },
    catalogEntries(state): ItemCatalogEntry[] {
      if (!state.catalog) return []
      return Object.values(state.catalog.Items).sort(
        (a, b) => a.SortId - b.SortId || a.StaticId.localeCompare(b.StaticId),
      )
    },
    catalogSearchTerms(state): Record<string, string> {
      if (!state.catalog) return {}
      const result: Record<string, string> = {}
      for (const group of state.catalog.Groups) {
        const searchable = group.SearchTerms.join(' ')
        for (const variant of group.Variants) result[variant.StaticId] = searchable
      }
      return result
    },
    filteredCatalog(): ItemCatalogEntry[] {
      const locale = useSessionStore().locale
      const query = this.query.trim().toLocaleLowerCase()
      const targetSlot = this.selectedSlot
      return this.catalogEntries.filter((item) => {
        const searchable = `${this.catalogSearchTerms[item.StaticId] || ''} ${item.I18n[locale]} ${item.I18n.en} ${item.I18n['zh-CN']} ${item.StaticId} ${item.Category} ${item.Rarity}`.toLocaleLowerCase()
        if (query && !searchable.includes(query)) return false
        if (this.category && item.Category !== this.category) return false
        if (this.rarity && String(item.Rarity) !== this.rarity) return false
        if (!item.AllowedContainers.includes(this.selectedContainer)) return false
        if (this.selectedContainer === 'drop') return false
        if (this.selectedContainer === 'weapon' && item.EquipSlot !== 'weapon') return false
        if (this.selectedContainer === 'armor' && targetSlot?.SlotType && item.EquipSlot !== targetSlot.SlotType) return false
        return true
      })
    },
    categories(): string[] {
      return [...new Set(this.catalogEntries.map((item) => item.Category))].sort()
    },
  },
  actions: {
    async loadCatalog() {
      if (this.catalog) return
      this.catalog = await apiClient.getItemCatalog()
    },
    async loadInventory(playerId: string, force = false) {
      if (!playerId) return
      if (!force && this.inventory?.PlayerId === playerId) return
      this.loading = true
      this.error = ''
      try {
        this.inventory = await apiClient.getPlayerInventory(playerId)
        this.selectedPlayerId = playerId
        this.ensureSelection()
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    selectContainer(container: ItemContainerName) {
      this.selectedContainer = container
      this.selectedSlotIndex = null
      this.query = ''
      this.category = ''
      this.rarity = ''
    },
    selectSlot(slotIndex: number) {
      this.selectedSlotIndex = slotIndex
    },
    async addItem(payload: {
      StaticId: string
      Container: ItemContainerName
      Quantity?: number
      SlotIndex?: number
      EggCharacterId?: string
    }) {
      return this.mutate(() => apiClient.createItem(this.selectedPlayerId, payload))
    },
    async patchSelected(changes: Record<string, number | string>) {
      if (this.selectedSlotIndex === null) throw new Error('No item slot is selected.')
      return this.mutate(() => apiClient.patchItem(
        this.selectedPlayerId,
        this.selectedContainer,
        this.selectedSlotIndex as number,
        changes,
      ))
    },
    async deleteSelected(confirmDangerous = false) {
      if (this.selectedSlotIndex === null) throw new Error('No item slot is selected.')
      return this.mutate(() => apiClient.deleteItem(
        this.selectedPlayerId,
        this.selectedContainer,
        this.selectedSlotIndex as number,
        confirmDangerous,
      ))
    },
    async move(
      source: { Container: ItemContainerName; SlotIndex: number },
      target: { Container: ItemContainerName; SlotIndex: number },
    ) {
      const result = await this.mutate(() => apiClient.moveItem(this.selectedPlayerId, source, target))
      this.selectedContainer = target.Container
      this.selectedSlotIndex = target.SlotIndex
      return result
    },
    async mutate(operation: () => Promise<ItemMutationResult>) {
      const result = await useDraftStore().runMutation(operation)
      this.inventory = result.Inventory
      useSessionStore().applyDirtyRevision(result.DirtyRevision)
      this.ensureSelection()
      return result
    },
    ensureSelection() {
      if (!this.inventory) {
        this.selectedSlotIndex = null
        return
      }
      const slots = this.inventory.Containers[this.selectedContainer].Slots
      if (this.selectedSlotIndex !== null && slots.some((slot) => slot.SlotIndex === this.selectedSlotIndex)) return
      this.selectedSlotIndex = slots.find((slot) => slot.Unlocked)?.SlotIndex ?? null
    },
    clear() {
      this.inventory = null
      this.selectedPlayerId = ''
      this.selectedContainer = 'common'
      this.selectedSlotIndex = null
      this.query = ''
      this.category = ''
      this.rarity = ''
      this.error = ''
    },
  },
})
