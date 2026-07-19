import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SearchableSelect from './SearchableSelect.vue'

const options = [
  {
    value: 'Anubis', title: '阿努比斯', subtitle: 'Anubis', meta: '图鉴 #100', badge: '帕鲁',
    iconUrl: '/image/pals/Anubis', searchText: 'Anubis 阿努比斯 100',
  },
  {
    value: 'WorldTreeDragon', title: '枯星龙', subtitle: 'WorldTreeDragon', meta: '图鉴 #204', badge: '帕鲁',
    iconUrl: '/image/pals/WorldTreeDragon', searchText: 'Astralym 枯星龙 WorldTreeDragon 204',
  },
  {
    value: 'Hunter_Rifle', title: '持枪猎人', subtitle: 'Hunter_Rifle', badge: '人类 NPC',
    searchText: 'Rifle Hunter 持枪猎人 Hunter_Rifle',
  },
]

function mountPicker(modelValue = 'Anubis') {
  return mount(SearchableSelect, {
    props: {
      modelValue, options, placeholder: '选择物种', searchPlaceholder: '搜索物种', emptyText: '没有结果',
    },
    global: { stubs: { AppIcon: { template: '<i />' } } },
  })
}

describe('SearchableSelect', () => {
  it('searches bilingual names, internal IDs, and Paldeck numbers', async () => {
    const wrapper = mountPicker()
    await wrapper.get('.select-trigger').trigger('click')
    const input = wrapper.get('input')

    await input.setValue('枯星')
    expect(wrapper.findAll('.select-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('WorldTreeDragon')

    await input.setValue('Hunter_Rifle')
    expect(wrapper.findAll('.select-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('人类 NPC')

    await input.setValue('204')
    expect(wrapper.findAll('.select-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('枯星龙')
  })

  it('supports arrow keys, Enter selection, and Escape closing', async () => {
    const wrapper = mountPicker()
    await wrapper.get('.select-trigger').trigger('click')
    const input = wrapper.get('input')
    await input.trigger('keydown', { key: 'ArrowDown' })
    await input.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['WorldTreeDragon'])
    expect(wrapper.find('.select-popover').exists()).toBe(false)

    await wrapper.get('.select-trigger').trigger('click')
    await wrapper.get('input').trigger('keydown', { key: 'Escape' })
    expect(wrapper.find('.select-popover').exists()).toBe(false)
  })

  it('renders an explicit no-results state', async () => {
    const wrapper = mountPicker()
    await wrapper.get('.select-trigger').trigger('click')
    await wrapper.get('input').setValue('not-a-species')
    expect(wrapper.text()).toContain('没有结果')
  })
})
