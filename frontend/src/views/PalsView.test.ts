import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useSessionStore } from '@/stores/session'
import PalsView from './PalsView.vue'

describe('PalsView species selection', () => {
  it('uses the bilingual searchable species picker when creating an object', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/pals', component: PalsView }] })
    await router.push('/pals')
    await router.isReady()
    const session = useSessionStore()
    session.initialized = true
    session.session.Loaded = true
    const catalog = useCatalogStore()
    catalog.loaded = true
    catalog.pals = [
      { InternalName: 'Anubis', Elements: ['Earth'], Invalid: false, Suitabilities: {}, I18n: { en: 'Anubis', 'zh-CN': '阿努比斯' }, SortingKey: '100', IsHuman: false, IconAccessKey: 'Anubis' },
      { InternalName: 'WorldTreeDragon', Elements: ['Dragon'], Invalid: false, Suitabilities: {}, I18n: { en: 'Astralym', 'zh-CN': '枯星龙' }, SortingKey: '204', IsHuman: false, IconAccessKey: 'WorldTreeDragon' },
      { InternalName: 'Hunter_Rifle', Elements: [], Invalid: false, Suitabilities: {}, I18n: { en: 'Rifle Hunter', 'zh-CN': '持枪猎人' }, SortingKey: null, IsHuman: true, IconAccessKey: 'Human' },
    ]
    const collection = useCollectionStore()
    collection.pals = [{ InstanceId: 'pal-1', CharacterID: 'Anubis', SpeciesKey: 'Anubis', SpeciesName: '阿努比斯', NickName: '', IconAccessKey: 'Anubis', PalDeckId: '100', Level: 1, Gender: null, OwnerPlayerUId: 'p1', OwnerName: 'Ray', ObjectType: 'pal', Location: 'palbox', Elements: ['Earth'], StateFlags: [], IsAnomalous: false }]
    collection.players = [{ PlayerUId: 'p1', InstanceId: 'i1', NickName: 'Ray', Level: 80, HasViewingCage: true, OtomoCharacterContainerId: 'o1', PalStorageContainerId: 's1', TechnologyPoint: 0, BossTechnologyPoint: 0, PalCount: 1 }]

    const wrapper = mount(PalsView, {
      global: {
        plugins: [pinia, router],
        stubs: {
          AppShell: { template: '<main><slot /></main>' }, AppIcon: { template: '<i />' }, StatusPill: { template: '<span><slot /></span>' }, VirtualPalGrid: { template: '<div />' },
          ModalDialog: { props: ['open', 'title', 'width'], template: '<section v-if="open" :data-width="width"><slot /><slot name="footer" /></section>' },
        },
      },
    })
    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text().includes('新增对象'))!.trigger('click')
    expect(wrapper.find('section[data-width="900px"]').exists()).toBe(true)
    expect(wrapper.get('.searchable-select').classes()).toContain('inline-grid')
    await wrapper.get('.select-trigger').trigger('click')
    await wrapper.get('.select-search input').setValue('204')
    expect(wrapper.findAll('.select-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('枯星龙')
    await wrapper.get('.select-search input').setValue('Hunter_Rifle')
    expect(wrapper.text()).toContain('人类 NPC')
  })
})
