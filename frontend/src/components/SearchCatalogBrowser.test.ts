import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SearchCatalogBrowser from './SearchCatalogBrowser.vue'

const options = [
  { value: 'Legend', title: '传说', subtitle: 'Legend', summary: '攻击、防御与移动速度提升', searchText: 'Legend 传说 attack defense 攻击 防御', meta: '评级 4' },
  { value: 'MutationPal_Mutant', title: '特殊体质', subtitle: 'MutationPal_Mutant', summary: '免疫中毒和灼烧伤害', searchText: 'Idiosyncratic 特殊体质 poison burn 免疫中毒 灼烧', badge: '突变专属', meta: '评级 4' },
]

describe('SearchCatalogBrowser', () => {
  it('searches skill descriptions and keeps mutation badges visible', async () => {
    const wrapper = mount(SearchCatalogBrowser, {
      props: { modelValue: '', options, searchPlaceholder: '搜索词条', emptyText: '没有结果' },
      global: { stubs: { AppIcon: { template: '<i />' } } },
    })
    await wrapper.get('input').setValue('中毒')
    expect(wrapper.findAll('.browser-results button')).toHaveLength(1)
    expect(wrapper.text()).toContain('突变专属')
    await wrapper.get('.browser-results button').trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['MutationPal_Mutant'])
  })
})
