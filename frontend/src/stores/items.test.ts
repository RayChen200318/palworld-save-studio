import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/apiClient'
import type { ItemCatalog, ItemCatalogEntry, ItemContainerName, PlayerInventory } from '@/types/domain'
import { useItemsStore } from './items'
import { useSessionStore } from './session'

const wood: ItemCatalogEntry = {
  StaticId: 'Wood', BaseKey: 'Wood', I18n: { en: 'Wood', 'zh-CN': '木材' }, Category: 'material',
  TypeA: 'Material', TypeB: 'MaterialWood', EquipSlot: null, AllowedContainers: ['common'],
  Rarity: 0, Rank: 1, SortId: 1, MaxStack: 9999, DynamicType: null, MaxDurability: 0,
  MagazineSize: 0, IconKey: 'wood', ManagedKind: 'normal',
}
const armor: ItemCatalogEntry = {
  ...wood, StaticId: 'ClothArmor', BaseKey: 'cloth', I18n: { en: 'Cloth Outfit', 'zh-CN': '布衣服' },
  Category: 'armor', EquipSlot: 'body', AllowedContainers: ['common', 'armor'], MaxStack: 1,
  DynamicType: 'armor', MaxDurability: 150,
}
const catalog: ItemCatalog = {
  Source: {}, Items: { Wood: wood, ClothArmor: armor }, Groups: [], EggSpecies: [],
}

function inventory(): PlayerInventory {
  const names: ItemContainerName[] = ['common', 'essential', 'food', 'weapon', 'armor', 'drop']
  return {
    PlayerId: 'p1', PlayerName: 'Ray',
    Containers: Object.fromEntries(names.map((name) => [name, {
      ContainerId: name, Capacity: name === 'armor' ? 1 : 2, PhysicalCapacity: name === 'armor' ? 1 : 2,
      UnlockedIndices: name === 'armor' ? [1] : [0, 1], ReadOnlyTarget: name === 'drop',
      Slots: name === 'armor'
        ? [{ Container: name, SlotIndex: 1, SlotType: 'body', Unlocked: true, Item: null }]
        : [0, 1].map((index) => ({ Container: name, SlotIndex: index, SlotType: null, Unlocked: true, Item: null })),
    }])) as PlayerInventory['Containers'],
  }
}

describe('item management store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('searches both languages and enforces the selected equipment slot', () => {
    const store = useItemsStore()
    store.catalog = catalog
    store.inventory = inventory()
    store.selectedContainer = 'armor'
    store.selectedSlotIndex = 1
    store.query = '布衣服'
    expect(store.filteredCatalog.map((item) => item.StaticId)).toEqual(['ClothArmor'])
    store.query = 'wood'
    expect(store.filteredCatalog).toEqual([])
  })

  it('searches the aggregated terms from every item variant', () => {
    const store = useItemsStore()
    store.catalog = {
      ...catalog,
      Groups: [{
        BaseKey: 'Gunpowder',
        I18n: { en: 'Gunpowder', 'zh-CN': '火药' },
        Category: 'material',
        IconKey: 'gunpowder',
        RepresentativeStaticId: 'Wood',
        Variants: [wood],
        SearchTerms: ['GunPowder2', '火药'],
        ManagedKind: 'normal',
      }],
    }
    store.inventory = inventory()
    store.query = '火药'
    expect(store.filteredCatalog.map((item) => item.StaticId)).toEqual(['Wood'])
  })

  it('applies exactly the dirty revision returned by a successful mutation', async () => {
    const store = useItemsStore()
    const next = inventory()
    store.inventory = next
    store.selectedPlayerId = 'p1'
    store.selectedContainer = 'common'
    store.selectedSlotIndex = 0
    vi.spyOn(apiClient, 'createItem').mockResolvedValue({ Inventory: next, DirtyRevision: 7 })

    await store.addItem({ StaticId: 'Wood', Container: 'common', Quantity: 2, SlotIndex: 0 })

    expect(useSessionStore().session.DirtyRevision).toBe(7)
    expect(useSessionStore().dirty).toBe(true)
  })
})
