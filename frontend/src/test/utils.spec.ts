/**
 * Unit tests for src/utils.ts — pure validation helpers.
 */
import { describe, it, expect } from 'vitest'
import { emailPattern, namePattern, passwordRules, confirmPasswordRules } from '@/utils'

// ── emailPattern ────────────────────────────────────────────────────
describe('emailPattern', () => {
  it('accepts a valid email', () => {
    expect(emailPattern.value.test('user@example.com')).toBe(true)
  })

  it('accepts email with sub-domain', () => {
    expect(emailPattern.value.test('u@sub.domain.org')).toBe(true)
  })

  it('rejects missing @', () => {
    expect(emailPattern.value.test('userexample.com')).toBe(false)
  })

  it('rejects missing TLD', () => {
    expect(emailPattern.value.test('user@')).toBe(false)
  })

  it('rejects empty string', () => {
    expect(emailPattern.value.test('')).toBe(false)
  })

  it('accepts plus addressing', () => {
    expect(emailPattern.value.test('user+tag@example.com')).toBe(true)
  })
})

// ── namePattern ─────────────────────────────────────────────────────
describe('namePattern', () => {
  it('accepts a simple name', () => {
    expect(namePattern.value.test('Anna')).toBe(true)
  })

  it('accepts names with spaces', () => {
    expect(namePattern.value.test('Anna Maria')).toBe(true)
  })

  it('accepts names with umlauts', () => {
    expect(namePattern.value.test('Müller')).toBe(true)
  })

  it('accepts names with accents', () => {
    expect(namePattern.value.test('José')).toBe(true)
  })

  it('rejects names with digits', () => {
    expect(namePattern.value.test('Anna123')).toBe(false)
  })

  it('rejects empty string', () => {
    expect(namePattern.value.test('')).toBe(false)
  })

  it('rejects names longer than 30 characters', () => {
    expect(namePattern.value.test('A'.repeat(31))).toBe(false)
  })

  it('accepts exactly 30 characters', () => {
    expect(namePattern.value.test('A'.repeat(30))).toBe(true)
  })
})

// ── passwordRules ───────────────────────────────────────────────────
describe('passwordRules', () => {
  it('returns required rule when isRequired=true', () => {
    const rules = passwordRules(true)
    expect(rules.required).toBe('Password is required')
  })

  it('does not include required when isRequired=false', () => {
    const rules = passwordRules(false)
    expect(rules.required).toBeUndefined()
  })

  it('requires minimum 8 characters', () => {
    const rules = passwordRules()
    expect(rules.minLength.value).toBe(8)
  })
})

// ── confirmPasswordRules ────────────────────────────────────────────
describe('confirmPasswordRules', () => {
  it('validates matching passwords', () => {
    const getValues = () => ({ password: 'secret123' })
    const rules = confirmPasswordRules(getValues)
    expect(rules.validate('secret123')).toBe(true)
  })

  it('rejects non-matching passwords', () => {
    const getValues = () => ({ password: 'secret123' })
    const rules = confirmPasswordRules(getValues)
    expect(rules.validate('wrong')).toBe('The passwords do not match')
  })

  it('works with new_password field', () => {
    const getValues = () => ({ new_password: 'newpass99' })
    const rules = confirmPasswordRules(getValues)
    expect(rules.validate('newpass99')).toBe(true)
  })

  it('returns required rule when isRequired=true', () => {
    const getValues = () => ({ password: '' })
    const rules = confirmPasswordRules(getValues, true)
    expect(rules.required).toBe('Password confirmation is required')
  })

  it('does not include required when isRequired=false', () => {
    const getValues = () => ({ password: '' })
    const rules = confirmPasswordRules(getValues, false)
    expect(rules.required).toBeUndefined()
  })
})

// ── formatBirthDateLocale ───────────────────────────────────────────
import { formatBirthDateLocale } from '@/utils'

describe('formatBirthDateLocale', () => {
  // null / undefined / empty input
  it('returns null for null input', () => {
    expect(formatBirthDateLocale(null, 'de')).toBeNull()
  })

  it('returns null for undefined input', () => {
    expect(formatBirthDateLocale(undefined, 'de')).toBeNull()
  })

  it('returns null for empty string', () => {
    expect(formatBirthDateLocale('', 'de')).toBeNull()
  })

  // German format output
  it('formats ISO date to German DD.MM.YYYY', () => {
    expect(formatBirthDateLocale('1990-05-16', 'de')).toBe('16.05.1990')
  })

  it('passes through already-German date unchanged for DE locale', () => {
    expect(formatBirthDateLocale('16.05.1990', 'de')).toBe('16.05.1990')
  })

  // English format output
  it('formats ISO date to English "Month Dth, YYYY"', () => {
    expect(formatBirthDateLocale('2000-01-01', 'en')).toBe('January 1st, 2000')
  })

  it('formats ISO date to English with "nd" suffix', () => {
    expect(formatBirthDateLocale('1985-03-02', 'en')).toBe('March 2nd, 1985')
  })

  it('formats ISO date to English with "rd" suffix', () => {
    expect(formatBirthDateLocale('2010-07-03', 'en')).toBe('July 3rd, 2010')
  })

  it('formats ISO date to English with "th" suffix for day 4', () => {
    expect(formatBirthDateLocale('2021-08-04', 'en')).toBe('August 4th, 2021')
  })

  it('formats ISO date to English with "th" suffix for day 11', () => {
    // 11th is a special case: even though 11 % 10 === 1, it uses "th"
    expect(formatBirthDateLocale('2021-06-11', 'en')).toBe('June 11th, 2021')
  })

  it('formats ISO date to English with "th" suffix for day 12', () => {
    expect(formatBirthDateLocale('2021-06-12', 'en')).toBe('June 12th, 2021')
  })

  it('formats ISO date to English with "th" suffix for day 13', () => {
    expect(formatBirthDateLocale('2021-06-13', 'en')).toBe('June 13th, 2021')
  })

  it('formats German-style date to English', () => {
    expect(formatBirthDateLocale('16.05.1990', 'en')).toBe('May 16th, 1990')
  })

  it('returns raw value for unrecognised date format', () => {
    expect(formatBirthDateLocale('not-a-date', 'de')).toBe('not-a-date')
  })

  it('handles all 12 months in English', () => {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December',
    ]
    months.forEach((name, i) => {
      const mm = String(i + 1).padStart(2, '0')
      const result = formatBirthDateLocale(`2000-${mm}-01`, 'en')
      expect(result).toBe(`${name} 1st, 2000`)
    })
  })
})
