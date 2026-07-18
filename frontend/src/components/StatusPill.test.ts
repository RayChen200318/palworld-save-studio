import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusPill from './StatusPill.vue'

describe('StatusPill', () => {
  it('renders its semantic tone and content', () => {
    const wrapper = mount(StatusPill, { props: { tone: 'green', dot: true }, slots: { default: 'Ready' } })
    expect(wrapper.classes()).toContain('tone-green')
    expect(wrapper.text()).toBe('Ready')
    expect(wrapper.find('i').exists()).toBe(true)
  })
})
