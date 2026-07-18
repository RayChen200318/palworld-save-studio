import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { useCollectionStore } from './collection'
import { useSessionStore } from './session'
import type { PalSummary } from '@/types/domain'

function pal(overrides: Partial<PalSummary>): PalSummary {
  return {
    InstanceId: 'id', CharacterID: 'WorldTreeDragon', SpeciesKey: 'WorldTreeDragon', SpeciesName: 'Astralym',
    NickName: '', IconAccessKey: 'WorldTreeDragon', PalDeckId: '200', Level: 1, Gender: null,
    OwnerPlayerUId: 'p1', OwnerName: 'Ray', ObjectType: 'pal', Location: 'palbox', Elements: ['Dragon'],
    StateFlags: [], IsAnomalous: false, ...overrides,
  }
}

describe('collection filters and sorting', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('searches name, internal id, owner, and instance id', () => {
    const store = useCollectionStore()
    store.pals = [pal({ InstanceId: 'alpha' }), pal({ InstanceId: 'beta', CharacterID: 'Hunter_Rifle', SpeciesName: 'Syndicate Gunner', OwnerName: 'Mia', ObjectType: 'human' })]
    store.filters.query = 'mia'
    expect(store.filteredPals.map((item) => item.InstanceId)).toEqual(['beta'])
    store.filters.query = 'worldtreedragon'
    expect(store.filteredPals.map((item) => item.InstanceId)).toEqual(['alpha'])
  })

  it('filters anomalies and sorts by descending level', () => {
    const store = useCollectionStore()
    store.pals = [pal({ InstanceId: 'a', Level: 12, IsAnomalous: true }), pal({ InstanceId: 'b', Level: 40, IsAnomalous: true }), pal({ InstanceId: 'c', Level: 80 })]
    store.filters.anomaly = 'yes'
    store.filters.sort = 'level'
    expect(store.filteredPals.map((item) => item.InstanceId)).toEqual(['b', 'a'])
  })

  it('keeps dashboard object statistics synchronized with collection edits', () => {
    const store = useCollectionStore()
    const session = useSessionStore()
    store.pals = [
      pal({ InstanceId: 'a' }),
      pal({ InstanceId: 'b', ObjectType: 'human', IsAnomalous: true }),
    ]

    store.syncSessionStatistics()

    expect(session.session.Statistics).toMatchObject({
      Pals: 1, Humans: 1, Anomalies: 1, Objects: 2,
    })
  })
})
