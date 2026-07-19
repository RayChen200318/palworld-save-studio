import { readdirSync, readFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = join(process.cwd(), 'src')

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return ['.css', '.vue'].includes(extname(entry.name)) ? [path] : []
  })
}

describe('0.3 typography system', () => {
  it('locks the approved brand palette and type scale', () => {
    const tokens = readFileSync(join(root, 'styles', 'tokens.css'), 'utf8').toLowerCase()
    for (const value of ['#080b14', '#0d1422', '#141e30', '#f4f7fb', '#aab7c8', '#35e6d1', '#8b7cff', '#55d6a5', '#f2c66d', '#ff7a8a']) {
      expect(tokens).toContain(value)
    }
    for (const value of ['--text-display: 40px', '--text-page: 28px', '--text-section: 18px', '--text-body: 15px', '--text-supporting: 13px', '--text-label: 12px', '--text-code: 11px']) {
      expect(tokens).toContain(value)
    }
  })

  it('does not reintroduce micro text below the 11px internal-ID floor', () => {
    const violations: string[] = []
    for (const path of sourceFiles(root)) {
      const text = readFileSync(path, 'utf8')
      for (const match of text.matchAll(/(?:font-size\s*:\s*|font\s*:\s*)(\d+(?:\.\d+)?)px/g)) {
        if (Number(match[1]) < 11) {
          violations.push(`${relative(root, path)}:${match.index}:${match[0]}`)
        }
      }
    }
    expect(violations).toEqual([])
  })

  it('reserves the 11px exception for internal IDs and code', () => {
    const violations: string[] = []
    for (const path of sourceFiles(root)) {
      const text = readFileSync(path, 'utf8')
      for (const rule of text.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
        const selector = rule[1].trim()
        for (const size of rule[2].matchAll(/(?:font-size\s*:\s*|font\s*:\s*)(\d+(?:\.\d+)?)px/g)) {
          if (Number(size[1]) >= 12) continue
          if (/code|small|\.slot-id|\.summary-card>p|\.player-hero p/.test(selector)) continue
          violations.push(`${relative(root, path)}:${selector}:${size[0]}`)
        }
      }
    }
    expect(violations).toEqual([])
  })

  it('keeps the readable root size at narrow desktop widths', () => {
    const base = readFileSync(join(root, 'styles', 'base.css'), 'utf8')
    expect(base).not.toMatch(/@media[^}]+\{[^}]*html[^}]*font-size/)
    expect(base).toContain('font-size: var(--text-body)')
  })
})
