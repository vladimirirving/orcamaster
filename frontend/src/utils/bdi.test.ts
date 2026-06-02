import { describe, it, expect } from 'vitest'
import { calcBdiComposto } from './bdi'

describe('calcBdiComposto', () => {
  it('ac=5% rest zero → 0.05', () => {
    const result = calcBdiComposto(0.05, 0, 0, 0, 0, 0, 0, 0)
    expect(result).toBeCloseTo(0.05, 5)
  })

  it('complex formula', () => {
    // ((1 + 0.04 + 0.01 + 0.02 + 0.01 + 0.08) / (1 - 0.03 - 0.0065 - 0.03)) - 1
    const result = calcBdiComposto(0.04, 0.01, 0.02, 0.01, 0.08, 0.03, 0.0065, 0.03)
    // numerator = 1.16, denominator = 0.9335 → 1.24 - 1 ≈ 0.2429...
    expect(result).toBeGreaterThan(0.24)
    expect(result).toBeLessThan(0.26)
  })

  it('throws when ISS+PIS+COFINS >= 1', () => {
    expect(() => calcBdiComposto(0, 0, 0, 0, 0, 0.5, 0.3, 0.2)).toThrow()
  })

  it('throws when denominator is negative', () => {
    expect(() => calcBdiComposto(0, 0, 0, 0, 0, 0.6, 0.3, 0.2)).toThrow()
  })
})
