import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { useDraftStore } from './draft'
import { useSessionStore } from './session'

describe('global draft state', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('blocks commit while a mutation request is pending', async () => {
    const draft = useDraftStore()
    const session = useSessionStore()
    session.applyDirtyRevision(2)
    let resolve!: () => void
    const operation = draft.runMutation(() => new Promise<void>((done) => { resolve = done }))
    expect(draft.pending).toBe(true)
    expect(draft.canCommit).toBe(false)
    resolve()
    await operation
    expect(draft.pending).toBe(false)
    expect(draft.canCommit).toBe(true)
  })
})
