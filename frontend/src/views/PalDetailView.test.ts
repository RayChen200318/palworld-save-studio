import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/apiClient'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useSessionStore } from '@/stores/session'
import type { PalDetail } from '@/types/domain'
import PalDetailView from './PalDetailView.vue'

const detail: PalDetail = {
  InstanceId: 'pal-1', CharacterID: 'Anubis', SpeciesKey: 'Anubis', SpeciesName: '阿努比斯', NickName: '', IconAccessKey: 'Anubis', PalDeckId: '100', Level: 80,
  Gender: 'EPalGenderType::Male', OwnerPlayerUId: 'p1', OwnerName: 'Ray', ObjectType: 'pal', Location: 'palbox', Elements: ['Earth'], StateFlags: [], IsAnomalous: false,
  group_id: null, ContainerId: 'box', SlotIndex: 0, DataAccessKey: 'Anubis', DisplayName: '阿努比斯', FriendshipLevel: 10,
  HasBaseVariant: true, HasBossVariant: true, HasTowerVariant: false, HasWorkerSick: false, IsFaintedPal: false, Is_Unref_Pal: false, in_owner_palbox: true,
  IsHuman: false, IsBOSS: false, IsRarePal: false, IsTower: false, IsRAID: false, IsPREDATOR: false, IsOilrig: false, IsExpeditionPal: false, IsAwakening: false,
  ComputedMaxHP: 1000, ComputedAttack: 500, ComputedDefense: 400, ComputedCraftSpeed: 100, Rank: 5, Rank_HP: 0, Rank_Attack: 0, Rank_Defence: 0, Rank_CraftSpeed: 0,
  Talent_HP: 100, Talent_Melee: 100, Talent_Shot: 100, Talent_Defense: 100, PassiveSkillList: ['Legend'], EquipWaza: ['EPalWazaID::PoisonFog'], MasteredWaza: ['EPalWazaID::PoisonFog'],
  Suitabilities: { 'EPalWorkSuitability::Handcraft': 7, 'EPalWorkSuitability::Mining': 7 },
}

async function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/pals/:id', component: PalDetailView }, { path: '/pals', component: { template: '<div />' } }] })
  await router.push('/pals/pal-1')
  await router.isReady()
  const session = useSessionStore()
  session.initialized = true
  session.session.Loaded = true
  const catalog = useCatalogStore()
  catalog.loaded = true
  catalog.pals = [
    { InternalName: 'Anubis', Elements: ['Earth'], Invalid: false, Suitabilities: { 'EPalWorkSuitability::Handcraft': 6, 'EPalWorkSuitability::Mining': 6 }, I18n: { en: 'Anubis', 'zh-CN': '阿努比斯' }, SortingKey: '100', IsHuman: false, IconAccessKey: 'Anubis' },
    { InternalName: 'BlueSkyDragon', Elements: ['Water'], Invalid: false, Suitabilities: { 'EPalWorkSuitability::Watering': 8 }, I18n: { en: 'Faleris Aqua', 'zh-CN': '水羽龙' }, SortingKey: '204', IsHuman: false, IconAccessKey: 'BlueSkyDragon' },
  ]
  catalog.passives = [
    { InternalName: 'Legend', I18n: { en: { Name: 'Legend', Description: 'Attack, defense and movement speed increase.' }, 'zh-CN': { Name: '传说', Description: '攻击、防御与移动速度提升。' } }, Rating: 4, IsMutationExclusive: false },
    { InternalName: 'MutationPal_Mutant', I18n: { en: { Name: 'Idiosyncratic', Description: 'Immune to poison and burn damage.' }, 'zh-CN': { Name: '特殊体质', Description: '免疫中毒与灼烧伤害。' } }, Rating: 4, IsMutationExclusive: true },
  ]
  catalog.actives = [
    { InternalName: 'EPalWazaID::PoisonFog', I18n: { en: { Name: 'Poison Fog', Description: 'Creates a poisonous fog.' }, 'zh-CN': { Name: '毒雾', Description: '于前方制造毒雾。' } }, HasSkillFruit: false, IsUniqueSkill: false, Power: 0, Element: 'Dark', CT: 30, Invalid: false },
    { InternalName: 'EPalWazaID::NoDescription', I18n: { en: { Name: 'Unknown Art', Description: '' }, 'zh-CN': { Name: '未知招式', Description: '' } }, HasSkillFruit: false, IsUniqueSkill: false, Power: 120, Element: 'Dragon', CT: 18, Invalid: false },
  ]
  const collection = useCollectionStore()
  collection.pals = [{ ...detail }]
  collection.players = [{ PlayerUId: 'p1', InstanceId: 'i1', NickName: 'Ray', Level: 80, HasViewingCage: true, OtomoCharacterContainerId: 'o1', PalStorageContainerId: 's1', TechnologyPoint: 0, BossTechnologyPoint: 0, PalCount: 1 }]
  vi.spyOn(apiClient, 'getPal').mockResolvedValue(detail)
  const wrapper = mount(PalDetailView, {
    global: {
      plugins: [pinia, router],
      stubs: { AppShell: { template: '<main><slot /></main>' }, AppIcon: { template: '<i />' }, StatusPill: { template: '<span><slot /></span>' }, ModalDialog: { props: ['open'], template: '<section v-if="open"><slot /></section>' } },
    },
  })
  await flushPromises()
  return { wrapper, session }
}

describe('PalDetailView 0.4 editor enhancements', () => {
  it('searches replacement species and exposes only legal work levels through ten', async () => {
    const { wrapper } = await mountView()
    await wrapper.get('.select-trigger').trigger('click')
    await wrapper.get('.select-search input').setValue('204')
    expect(wrapper.text()).toContain('水羽龙')

    await wrapper.findAll('.tabs button').find((button) => button.text() === '工作')!.trigger('click')
    const values = wrapper.findAll('.work-grid select').at(0)!.findAll('option').map((option) => option.attributes('value'))
    expect(values).toEqual(['7', '8', '9', '10'])
  })

  it('shows passive effects, mutation filtering, active metrics, and missing descriptions', async () => {
    const { wrapper, session } = await mountView()
    await wrapper.findAll('.tabs button').find((button) => button.text() === '被动技能')!.trigger('click')
    expect(wrapper.text()).toContain('攻击、防御与移动速度提升')
    await wrapper.findAll('.skill-filter button').find((button) => button.text() === '突变专属')!.trigger('click')
    expect(wrapper.text()).toContain('特殊体质')
    expect(wrapper.text()).toContain('免疫中毒与灼烧伤害')

    await wrapper.findAll('.tabs button').find((button) => button.text() === '主动技能')!.trigger('click')
    expect(wrapper.text()).toContain('于前方制造毒雾')
    expect(wrapper.text()).toContain('威力 120')
    expect(wrapper.text()).toContain('游戏数据未提供描述')

    session.locale = 'en'
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Poison Fog')
    expect(wrapper.text()).toContain('Game data does not provide a description')
  })
})
