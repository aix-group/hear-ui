/**
 * Unit tests for the Vuetify theme plugin.
 */
import { describe, it, expect } from 'vitest'
import { lightTheme } from './theme'

describe('theme.ts', () => {
  it('exports lightTheme', () => {
    expect(lightTheme).toBeDefined()
  })

  it('lightTheme is not dark', () => {
    expect(lightTheme.dark).toBe(false)
  })

  it('lightTheme has required colors', () => {
    expect(lightTheme.colors).toBeDefined()
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['primary']).toBeDefined()
    expect(colors['secondary']).toBeDefined()
    expect(colors['error']).toBeDefined()
    expect(colors['success']).toBeDefined()
    expect(colors['warning']).toBeDefined()
  })

  it('lightTheme primary color is a valid hex color', () => {
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['primary']).toMatch(/^#[0-9A-Fa-f]{6}$/)
  })

  it('lightTheme has background and surface colors', () => {
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['background']).toBe('#FFFFFF')
    expect(colors['surface']).toBe('#FFFFFF')
  })

  it('lightTheme has logo_red color', () => {
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['logo_red']).toBe('#DD054A')
  })

  it('lightTheme has info color', () => {
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['info']).toBeDefined()
    expect(colors['info']).toMatch(/^#[0-9A-Fa-f]{6}$/)
  })

  it('lightTheme has accent color', () => {
    const colors = lightTheme.colors as Record<string, string>
    expect(colors['accent']).toBe('#A78BFA')
  })
})
