/**
 * Unit tests for the useCustomToast composable and toaster module.
 */
import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'
import { toaster } from '@/components/ui/toaster'
import useCustomToast from '@/hooks/useCustomToast'
import * as loggerModule from '@/lib/logger'

describe('toaster', () => {
  it('has a create method', () => {
    expect(typeof toaster.create).toBe('function')
  })

  it('create() logs via logger in DEV mode', () => {
    const spy = vi.spyOn(loggerModule.logger, 'info').mockImplementation(() => {})
    // Force DEV mode so the log branch executes
    const originalDev = import.meta.env.DEV
    ;(import.meta.env as Record<string, unknown>).DEV = true
    toaster.create({ title: 'Test', description: 'Hello', type: 'success' })
    expect(spy).toHaveBeenCalledWith('TOAST', 'Test', 'Hello', 'success')
    ;(import.meta.env as Record<string, unknown>).DEV = originalDev
    spy.mockRestore()
  })
})

describe('useCustomToast', () => {
  let createSpy: MockInstance<Parameters<typeof toaster.create>, ReturnType<typeof toaster.create>>

  beforeEach(() => {
    createSpy = vi.spyOn(toaster, 'create').mockImplementation(() => {})
  })

  it('showSuccessToast calls toaster.create with type success', () => {
    const { showSuccessToast } = useCustomToast()
    showSuccessToast('It worked!')
    expect(createSpy).toHaveBeenCalledWith({
      title: 'Success!',
      description: 'It worked!',
      type: 'success',
    })
  })

  it('showErrorToast calls toaster.create with type error', () => {
    const { showErrorToast } = useCustomToast()
    showErrorToast('Something broke')
    expect(createSpy).toHaveBeenCalledWith({
      title: 'Something went wrong!',
      description: 'Something broke',
      type: 'error',
    })
  })
})
