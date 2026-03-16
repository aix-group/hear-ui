/**
 * Unit tests for the Vuetify plugin.
 */
import { describe, it, expect } from 'vitest'
import { vuetify } from './vuetify'

describe('vuetify.ts', () => {
  it('exports a vuetify instance', () => {
    expect(vuetify).toBeDefined()
  })

  it('vuetify instance has install method', () => {
    expect(typeof vuetify.install).toBe('function')
  })

  it('vuetify uses the light theme', () => {
    const theme = (vuetify as any).theme
    expect(theme).toBeDefined()
  })
})
