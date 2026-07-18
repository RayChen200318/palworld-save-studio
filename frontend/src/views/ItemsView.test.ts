import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/apiClient'
import { useCollectionStore } from '@/stores/collection'
import { useItemsStore } from '@/stores/items'
import { useSessionStore } from '@/stores/session'
import type { ItemCatalog, ItemContainerName, ItemSlotItem, PlayerInventory } from '@/types/domain'
import ItemsView from './ItemsView.vue'

const item = (overrides: Partial<ItemSlotItem> = {}): ItemSlotItem => ({
  StaticId: 'Wood', I18n: { en: 'Wood', 'zh-CN': '木材' }, IconKey: 'wood', Category: 'material',
  Quantity: 12, MaxStack: 9999, Rarity: 0, Variants: [], DynamicId: null, DynamicType: null,
  Durability: null, MaxDurability: 0, Ammo: null, MagazineSize: 0, PassiveSkills: [],
  EggCharacterId: null, StateFlags: [], ...overrides,
})

function inventory(playerId = 'p1'): PlayerInventory {
  const names: ItemContainerName[] = ['common', 'essential', 'food', 'weapon', 'armor', 'drop']
  const containers = Object.fromEntries(names.map((name) => {
    const slots = name === 'common'
      ? [
          { Container: name, SlotIndex: 0, SlotType: null, Unlocked: true, Item: item() },
          { Container: name, SlotIndex: 1, SlotType: null, Unlocked: true, Item: null },
          { Container: name, SlotIndex: 2, SlotType: null, Unlocked: true, Item: item({ StaticId: 'Mod_Item', I18n: { en: 'Mod_Item', 'zh-CN': 'Mod_Item' }, IconKey: null, Category: 'unknown', MaxStack: null, StateFlags: ['unknown-item'] }) },
        ]
      : []
    return [name, {
      ContainerId: name, Capacity: slots.length, PhysicalCapacity: slots.length,
      UnlockedIndices: slots.map((slot) => slot.SlotIndex), Slots: slots, ReadOnlyTarget: name === 'drop',
    }]
  })) as PlayerInventory['Containers']
  return { PlayerId: playerId, PlayerName: playerId === 'p1' ? 'Ray' : 'Mia', Containers: containers }
}

const catalog: ItemCatalog = {
  Source: {},
  Items: {
    Wood: {
      StaticId: 'Wood', BaseKey: 'Wood', I18n: { en: 'Wood', 'zh-CN': '木材' }, Category: 'material',
      TypeA: 'Material', TypeB: 'MaterialWood', EquipSlot: null, AllowedContainers: ['common'],
      Rarity: 0, Rank: 1, SortId: 1, MaxStack: 9999, DynamicType: null, MaxDurability: 0,
      MagazineSize: 0, IconKey: 'wood',
    },
  },
  Groups: [], EggSpecies: [],
}

async function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/items', component: ItemsView }] })
  await router.push('/items')
  await router.isReady()
  const session = useSessionStore()
  session.initialized = true
  session.session.Loaded = true
  const collection = useCollectionStore()
  collection.players = [
    { PlayerUId: 'p1', InstanceId: 'i1', NickName: 'Ray', Level: 80, HasViewingCage: true, OtomoCharacterContainerId: 'o1', PalStorageContainerId: 's1', TechnologyPoint: 0, BossTechnologyPoint: 0, PalCount: 0 },
    { PlayerUId: 'p2', InstanceId: 'i2', NickName: 'Mia', Level: 70, HasViewingCage: true, OtomoCharacterContainerId: 'o2', PalStorageContainerId: 's2', TechnologyPoint: 0, BossTechnologyPoint: 0, PalCount: 0 },
  ]
  const store = useItemsStore()
  store.catalog = catalog
  store.inventory = inventory()
  store.selectedPlayerId = 'p1'
  store.selectedSlotIndex = 0
  const wrapper = mount(ItemsView, {
    global: {
      plugins: [pinia, router],
      stubs: {
        AppShell: { props: ['eyebrow', 'title'], template: '<main><slot /></main>' },
        AppIcon: { template: '<i />' },
        StatusPill: { template: '<span><slot /></span>' },
        ModalDialog: { props: ['open', 'title'], emits: ['close'], template: '<section v-if="open"><h2>{{ title }}</h2><slot /><footer><slot name="footer" /></footer></section>' },
      },
    },
  })
  await flushPromises()
  return { wrapper, store }
}

describe('ItemsView', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders real and unknown slots and opens the searchable add drawer', async () => {
    const { wrapper, store } = await mountView()
    expect(wrapper.text()).toContain('木材')
    expect(wrapper.findAll('.item-slot.anomalous')).toHaveLength(1)

    store.selectSlot(1)
    await wrapper.vm.$nextTick()
    const addButtons = wrapper.findAll('button').filter((button) => button.text().includes('添加到此槽位'))
    expect(addButtons).toHaveLength(1)
    await addButtons[0].trigger('click')

    expect(wrapper.text()).toContain('新增正式物品')
    expect(wrapper.text()).toContain('Wood')
  })

  it('routes drag-drop and detail changes through atomic item mutations', async () => {
    const { wrapper } = await mountView()
    const moved = inventory()
    moved.Containers.common.Slots[1].Item = moved.Containers.common.Slots[0].Item
    moved.Containers.common.Slots[0].Item = null
    const moveSpy = vi.spyOn(apiClient, 'moveItem').mockResolvedValue({ Inventory: moved, DirtyRevision: 2 })
    const patchSpy = vi.spyOn(apiClient, 'patchItem').mockResolvedValue({ Inventory: inventory(), DirtyRevision: 3 })
    const slots = wrapper.findAll('.item-slot')

    await slots[0].trigger('dragstart')
    await slots[1].trigger('drop')
    await flushPromises()
    expect(moveSpy).toHaveBeenCalledWith('p1', { Container: 'common', SlotIndex: 0 }, { Container: 'common', SlotIndex: 1 })

    useItemsStore().selectedSlotIndex = 0
    useItemsStore().inventory = inventory()
    await wrapper.vm.$nextTick()
    await wrapper.get('.detail-fields input').setValue(20)
    await flushPromises()
    expect(patchSpy).toHaveBeenCalledWith('p1', 'common', 0, { Quantity: 20 })
    expect(useSessionStore().session.DirtyRevision).toBe(3)
  })

  it('loads the newly selected player inventory', async () => {
    const { wrapper } = await mountView()
    const loadSpy = vi.spyOn(apiClient, 'getPlayerInventory').mockResolvedValue(inventory('p2'))

    await wrapper.get('.player-field select').setValue('p2')
    await flushPromises()

    expect(loadSpy).toHaveBeenCalledWith('p2')
    expect(useItemsStore().selectedPlayerId).toBe('p2')
  })
})
