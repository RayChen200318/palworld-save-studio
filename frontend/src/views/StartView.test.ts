import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiClient } from '@/services/apiClient'
import { useSessionStore } from '@/stores/session'
import type { PathContext } from '@/types/domain'
import StartView from './StartView.vue'

const cContext: PathContext = {
  currentPath: 'C:\\Users\\Ray\\SaveGames',
  roots: ['C:\\', 'D:\\', 'Z:\\'],
  children: {
    'C:\\Users\\Ray\\SaveGames\\World': { filename: 'World', isDir: true },
    'C:\\Users\\Ray\\SaveGames\\readme.txt': { filename: 'readme.txt', isDir: false },
  },
  isPalDir: false,
}

const dContext: PathContext = {
  currentPath: 'D:\\Palworld\\Saved\\World',
  roots: ['C:\\', 'D:\\', 'Z:\\'],
  children: {},
  isPalDir: true,
}

const uncContext: PathContext = {
  currentPath: '\\\\server\\share\\Palworld\\World',
  roots: ['C:\\', 'D:\\', 'Z:\\'],
  children: {},
  isPalDir: true,
}

async function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: StartView }],
  })
  await router.push('/')
  await router.isReady()
  const session = useSessionStore()
  session.initialized = true
  const wrapper = mount(StartView, {
    global: {
      plugins: [pinia, router],
      stubs: {
        AppIcon: { template: '<i />' },
        BrandLockup: { template: '<div />' },
        LanguageToggle: { template: '<button type="button">language</button>' },
        StatusPill: { template: '<span><slot /></span>' },
        ModalDialog: {
          props: ['open', 'title', 'width'],
          emits: ['close'],
          template: '<section v-if="open" class="test-modal" :data-width="width"><slot /><footer><slot name="footer" /></footer></section>',
        },
      },
    },
  })
  return { wrapper, session }
}

async function openBrowser(wrapper: Awaited<ReturnType<typeof mountView>>['wrapper']) {
  const choose = wrapper.findAll('button').find((button) => button.text().includes('选择存档文件夹'))
  expect(choose).toBeDefined()
  await choose!.trigger('click')
  await flushPromises()
}

describe('StartView path browser', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('shows available drives, highlights the current drive, and switches drives', async () => {
    vi.spyOn(apiClient, 'getPathContext').mockResolvedValue(cContext)
    const browse = vi.spyOn(apiClient, 'browsePath').mockResolvedValue(dContext)
    const { wrapper } = await mountView()

    await openBrowser(wrapper)
    const roots = wrapper.findAll('.root-list button')
    expect(roots.map((button) => button.text())).toEqual(['C:', 'D:', 'Z:'])
    expect(roots[0].classes()).toContain('active')
    expect(wrapper.get<HTMLInputElement>('.direct-path input').element.value).toBe(cContext.currentPath)
    expect(wrapper.findAll('button').find((button) => button.text().includes('使用此文件夹'))!.attributes('disabled')).toBeDefined()

    await roots[1].trigger('click')
    await flushPromises()

    expect(browse).toHaveBeenCalledWith('D:\\')
    expect(wrapper.findAll('.root-list button')[1].classes()).toContain('active')
    expect(wrapper.get<HTMLInputElement>('.direct-path input').element.value).toBe(dContext.currentPath)
    expect(wrapper.findAll('button').find((button) => button.text().includes('使用此文件夹'))!.attributes('disabled')).toBeUndefined()
  })

  it('submits a pasted UNC path through the Enter-capable path form', async () => {
    vi.spyOn(apiClient, 'getPathContext').mockResolvedValue(cContext)
    const browse = vi.spyOn(apiClient, 'browsePath').mockResolvedValue(uncContext)
    const { wrapper } = await mountView()
    await openBrowser(wrapper)

    const input = wrapper.get<HTMLInputElement>('.direct-path input')
    await input.setValue('  \\\\server\\share\\Palworld\\World  ')
    expect(wrapper.get('.direct-path').element.tagName).toBe('FORM')
    await input.trigger('keydown.enter')
    await flushPromises()

    expect(browse).toHaveBeenCalledWith('\\\\server\\share\\Palworld\\World')
    expect(input.element.value).toBe(uncContext.currentPath)
    expect(wrapper.text()).toContain(uncContext.currentPath)
  })

  it('keeps the last successful directory and shows localized path errors', async () => {
    vi.spyOn(apiClient, 'getPathContext').mockResolvedValue(cContext)
    const browse = vi.spyOn(apiClient, 'browsePath').mockRejectedValue(new ApiError('missing', 404))
    const { wrapper, session } = await mountView()
    await openBrowser(wrapper)

    await wrapper.findAll('.root-list button')[1].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('路径不存在，或网络位置当前不可达。')
    expect(wrapper.text()).toContain(cContext.currentPath)
    expect(wrapper.get<HTMLInputElement>('.direct-path input').element.value).toBe(cContext.currentPath)
    expect(wrapper.find('.test-modal').exists()).toBe(true)

    session.locale = 'en'
    browse.mockRejectedValue(new ApiError('denied', 403))
    await wrapper.findAll('.root-list button')[2].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Permission was denied. Connect to the location in Windows first.')
  })

  it('disables navigation and confirmation controls while browsing', async () => {
    vi.spyOn(apiClient, 'getPathContext').mockResolvedValue({ ...cContext, isPalDir: true })
    let resolveBrowse!: (context: PathContext) => void
    vi.spyOn(apiClient, 'browsePath').mockReturnValue(new Promise((resolve) => { resolveBrowse = resolve }))
    const { wrapper } = await mountView()
    await openBrowser(wrapper)

    await wrapper.findAll('.root-list button')[1].trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('.root-list button').every((button) => button.attributes('disabled') !== undefined)).toBe(true)
    expect(wrapper.get('.direct-path input').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.direct-path button').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.browser-tools button').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.folder-list button').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('footer button').every((button) => button.attributes('disabled') !== undefined)).toBe(true)

    resolveBrowse(dContext)
    await flushPromises()
  })
})
