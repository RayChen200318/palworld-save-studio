import { describe, expect, it } from 'vitest'
import { computeVirtualWindow } from './virtualGrid'

describe('computeVirtualWindow', () => {
  it('keeps four overscan rows before and after the viewport', () => {
    const result = computeVirtualWindow(1000, 4, 200, 600, 2000, 4)
    expect(result.startRow).toBe(6)
    expect(result.endRow).toBe(17)
    expect(result.startIndex).toBe(24)
    expect(result.endIndex).toBe(68)
  })

  it('clamps the first and last windows without negative padding', () => {
    const first = computeVirtualWindow(10, 3, 200, 600, 0, 4)
    expect(first.startRow).toBe(0)
    expect(first.paddingTop).toBe(0)
    const last = computeVirtualWindow(10, 3, 200, 600, 5000, 4)
    expect(last.endIndex).toBe(10)
    expect(last.paddingBottom).toBe(0)
  })
})
