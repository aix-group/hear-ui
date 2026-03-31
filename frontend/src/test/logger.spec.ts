import { describe, it, expect, vi } from 'vitest'
import { logger } from '../lib/logger'

describe('logger', () => {
  it('has debug, info, warn, error methods', () => {
    expect(typeof logger.debug).toBe('function')
    expect(typeof logger.info).toBe('function')
    expect(typeof logger.warn).toBe('function')
    expect(typeof logger.error).toBe('function')
  })

  it('logger.error calls console.error with prefix', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('test error')
    expect(spy).toHaveBeenCalledWith('[hear-ui]', 'test error')
    spy.mockRestore()
  })

  it('logger.warn calls console.warn with prefix', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('test warning')
    expect(spy).toHaveBeenCalledWith('[hear-ui]', 'test warning')
    spy.mockRestore()
  })

  it('logger.info calls console.info with prefix', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {})
    logger.info('test info')
    expect(spy).toHaveBeenCalledWith('[hear-ui]', 'test info')
    spy.mockRestore()
  })

  it('logger.debug calls console.debug with prefix', () => {
    const spy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('test debug')
    expect(spy).toHaveBeenCalledWith('[hear-ui]', 'test debug')
    spy.mockRestore()
  })

  it('passes multiple arguments', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('msg', { detail: 42 })
    expect(spy).toHaveBeenCalledWith('[hear-ui]', 'msg', { detail: 42 })
    spy.mockRestore()
  })
})
