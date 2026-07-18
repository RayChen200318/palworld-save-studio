import { describe, expect, it } from 'vitest'
import { messages } from './messages'
import { mockPals, mockSave } from '@/mocks/session'

function keyShape(value: unknown, prefix = ''): string[] {
  if (Array.isArray(value)) return [prefix]
  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) =>
      keyShape(child, prefix ? `${prefix}.${key}` : key),
    )
  }
  return [prefix]
}

describe('translations', () => {
  it('has complete English coverage for every Chinese key', () => {
    expect(keyShape(messages.en).sort()).toEqual(keyShape(messages['zh-CN']).sort())
  })

  it('does not expose empty strings', () => {
    for (const locale of Object.values(messages)) {
      const serialized = JSON.stringify(locale)
      expect(serialized).not.toContain('\"\"')
    }
  })

  it('localizes every mock-data label shown in the preview', () => {
    for (const locale of ['zh-CN', 'en'] as const) {
      expect(mockSave.name[locale]).not.toBe('')
      expect(mockSave.updatedAt[locale]).not.toBe('')
      for (const pal of mockPals) {
        expect(pal.name[locale]).not.toBe('')
        expect(pal.element[locale]).not.toBe('')
      }
    }
  })
})
