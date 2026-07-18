import { describe, expect, it } from 'vitest'
import { messages } from './messages'

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

  it('defines all six function cards in both languages', () => {
    for (const locale of Object.values(messages)) {
      expect(locale.start.featureNames).toHaveLength(6)
      expect(locale.start.featureCopy).toHaveLength(6)
    }
  })

  it('keeps backup and rollback language out of product marketing', () => {
    const publicCopy = JSON.stringify({
      zh: {
        common: messages['zh-CN'].common,
        start: messages['zh-CN'].start,
        dashboard: messages['zh-CN'].dashboard,
        pals: messages['zh-CN'].pals,
        pal: messages['zh-CN'].pal,
        players: messages['zh-CN'].players,
        technology: messages['zh-CN'].technology,
      },
      en: {
        common: messages.en.common,
        start: messages.en.start,
        dashboard: messages.en.dashboard,
        pals: messages.en.pals,
        pal: messages.en.pal,
        players: messages.en.players,
        technology: messages.en.technology,
      },
    })
    expect(publicCopy).not.toMatch(/回退|安全写回|备份卖点|reversible|safe write-back|backup/i)
  })
})
