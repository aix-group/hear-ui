/**
 * Unit tests for the installI18n function in i18n.ts.
 * This is in a separate file to avoid contaminating the shared i18next
 * instance used by other tests.
 */
import { describe, it, expect } from 'vitest'
import { createApp } from 'vue'
import installI18n from '../i18n'

describe('installI18n (i18n.ts)', () => {
  it('returns the Vue app after installation', () => {
    const app = createApp({ template: '<div />' })
    const result = installI18n(app)
    expect(result).toBe(app)
  })

  it('installs i18next-vue plugin on the app', () => {
    const app = createApp({ template: '<div />' })
    const useSpy: string[] = []
    const originalUse = app.use.bind(app)
    app.use = (plugin: any, ...opts: any[]) => {
      useSpy.push(typeof plugin === 'object' ? plugin?.install?.name ?? 'plugin' : String(plugin))
      return originalUse(plugin, ...opts)
    }
    installI18n(app)
    expect(useSpy.length).toBeGreaterThan(0)
  })
})
