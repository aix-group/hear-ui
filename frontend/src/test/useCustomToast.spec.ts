/**
 * Unit tests for the useCustomToast composable and toaster module.
 */
import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'
import { toaster } from '@/components/ui/toaster'
import useCustomToast from '@/hooks/useCustomToast'

describe('toaster', () => {
  it('has a create method', () => {
    expect(typeof toaster.create).toBe('function')
  })

  it('create() logs to console', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {})
    toaster.create({ title: 'Test', description: 'Hello', type: 'success' })
    expect(spy).toHaveBeenCalledWith('TOAST', 'Test', 'Hello', 'success')
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
