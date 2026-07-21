import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/apiClient'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useItemsStore } from '@/stores/items'
import { useSessionStore } from '@/stores/session'
import type { ItemCatalog, ItemContainerName, ItemSlotItem, PlayerInventory } from '@/types/domain'
import ItemsView from './ItemsView.vue'

const item = (overrides: Partial<ItemSlotItem> = {}): ItemSlotItem => ({
  StaticId: 'Wood', ManagedKind: 'normal', I18n: { en: 'Wood', 'zh-CN': '木材' }, IconKey: 'wood', Category: 'material',
  Quantity: 12, MaxStack: 9999, Rarity: 0, Variants: [], DynamicId: null, DynamicType: null,
  Durability: null, MaxDurability: 0, Ammo: null, MagazineSize: 0, PassiveSkills: [],
  EggCharacterId: null, StateFlags: [], ...overrides,
})

function inventory(playerId = 'p1'): PlayerInventory {
  const names: ItemContainerName[] = ['common', 'essential', 'food', 'weapon', 'armor', 'drop']
  const containers = Object.fromEntries(names.map((name) => {
    const slots = name === 'common' ? [
          { Container: name, SlotIndex: 0, SlotType: null, Unlocked: true, Item: item() },
          { Container: name, SlotIndex: 1, SlotType: null, Unlocked: true, Item: null },
          { Container: name, SlotIndex: 2, SlotType: null, Unlocked: true, Item: item({ StaticId: 'Mod_Item', I18n: { en: 'Mod_Item', 'zh-CN': 'Mod_Item' }, IconKey: null, Category: 'unknown', MaxStack: null, StateFlags: ['unknown-item'] }) },
        ] : name === 'essential' ? [
          { Container: name, SlotIndex: 0, SlotType: null, Unlocked: true, Item: item({ StaticId: 'SkillUnlock_IceHorse', I18n: { en: 'Frostallion Saddle', 'zh-CN': '唤冬兽的鞍具' }, IconKey: 'saddle', Category: 'key', Quantity: 3, MaxStack: 1, StateFlags: ['invalid-quantity'] }) },
          { Container: name, SlotIndex: 1, SlotType: null, Unlocked: true, Item: null },
        ] : []
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
      MagazineSize: 0, IconKey: 'wood', ManagedKind: 'normal',
    },
    Egg_Dark: {
      StaticId: 'Egg_Dark', BaseKey: 'Egg_Dark', I18n: { en: 'Dark Egg', 'zh-CN': '暗黑蛋' }, Category: 'egg',
      TypeA: 'Consume', TypeB: 'PalEgg', EquipSlot: null, AllowedContainers: ['common'],
      Rarity: 0, Rank: 1, SortId: 2, MaxStack: 1, DynamicType: 'egg', MaxDurability: 0,
      MagazineSize: 0, IconKey: 'egg_dark', ManagedKind: 'normal',
    },
    SkillUnlock_IceHorse: {
      StaticId: 'SkillUnlock_IceHorse', BaseKey: 'Frostallion_Saddle', I18n: { en: 'Frostallion Saddle', 'zh-CN': '唤冬兽的鞍具' }, Category: 'key',
      TypeA: 'Essential', TypeB: 'Essential_PalGear', EquipSlot: null, AllowedContainers: ['essential'],
      Rarity: 4, Rank: 0, SortId: 3, MaxStack: 1, DynamicType: null, MaxDurability: 0,
      MagazineSize: 0, IconKey: 'saddle', ManagedKind: 'normal',
    },
  },
  Groups: [], EggSpecies: [
    { CharacterId: 'Anubis', I18n: { en: 'Anubis', 'zh-CN': '阿努比斯' }, IconAccessKey: 'Anubis' },
    { CharacterId: 'WorldTreeDragon', I18n: { en: 'Astralym', 'zh-CN': '枯星龙' }, IconAccessKey: 'WorldTreeDragon' },
  ],
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
  const palCatalog = useCatalogStore()
  palCatalog.loaded = true
  palCatalog.pals = [
    { InternalName: 'Anubis', Elements: ['Earth'], Invalid: false, Suitabilities: {}, I18n: { en: 'Anubis', 'zh-CN': '阿努比斯' }, SortingKey: '100', IsHuman: false, IconAccessKey: 'Anubis' },
    { InternalName: 'WorldTreeDragon', Elements: ['Dragon'], Invalid: false, Suitabilities: {}, I18n: { en: 'Astralym', 'zh-CN': '枯星龙' }, SortingKey: '204', IsHuman: false, IconAccessKey: 'WorldTreeDragon' },
  ]
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

  it('labels and repairs an existing invalid Pal Gear quantity', async () => {
    const { wrapper, store } = await mountView()
    store.selectContainer('essential')
    store.selectSlot(0)
    await wrapper.vm.$nextTick()
    const repaired = inventory()
    const repairedItem = repaired.Containers.essential.Slots[0].Item!
    repairedItem.Quantity = 1
    repairedItem.StateFlags = []
    const patchSpy = vi.spyOn(apiClient, 'patchItem').mockResolvedValue({ Inventory: repaired, DirtyRevision: 4 })

    expect(wrapper.text()).toContain('物品数量异常')
    await wrapper.get('.repair-card button').trigger('click')
    await flushPromises()

    expect(patchSpy).toHaveBeenCalledWith('p1', 'essential', 0, { Quantity: 1 })
    expect(useSessionStore().session.DirtyRevision).toBe(4)
  })

  it('searches legal egg species by bilingual name and Paldeck number', async () => {
    const { wrapper, store } = await mountView()
    store.selectSlot(1)
    await wrapper.vm.$nextTick()
    await wrapper.findAll('button').find((button) => button.text().includes('添加到此槽位'))!.trigger('click')
    await wrapper.findAll('.catalog-list button').find((button) => button.text().includes('暗黑蛋'))!.trigger('click')
    await wrapper.get('.add-options .select-trigger').trigger('click')
    await wrapper.get('.add-options .select-search input').setValue('204')
    expect(wrapper.findAll('.add-options .select-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('枯星龙')
    await wrapper.get('.add-options .select-search input').setValue('Anubis')
    expect(wrapper.text()).toContain('阿努比斯')
  })

  it('renders system progress records as read-only', async () => {
    const { wrapper, store } = await mountView()
    store.inventory!.Containers.common.Slots[0].Item = item({
      StaticId: 'BossDefeatReward_Test',
      ManagedKind: 'system',
      I18n: { en: 'BossDefeatReward_Test', 'zh-CN': 'BossDefeatReward_Test' },
      StateFlags: ['system-managed'],
    })
    store.selectSlot(0)
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('系统记录')
    expect(wrapper.find('.system-card').exists()).toBe(true)
    expect(wrapper.find('.detail-fields').exists()).toBe(false)
    expect(wrapper.find('.move-block').exists()).toBe(false)
    expect(wrapper.find('.delete-button').exists()).toBe(false)
    expect(wrapper.findAll('.item-slot')[0].attributes('draggable')).toBe('false')
  })
})
