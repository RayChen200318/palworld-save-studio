import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { usePrototypeStore } from './prototype'

describe('prototype draft state', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('keeps edits dirty until save confirmation', () => {
    const store = usePrototypeStore()
    store.markDirty()
    expect(store.dirty).toBe(true)
    store.saveDraft()
    expect(store.dirty).toBe(false)
    expect(store.lastSavedAt).not.toBe('')
  })
})
