import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll } from 'vitest'
import { getServer } from './mocks/server'

let server: any

beforeAll(async () => {
  server = await getServer()
  if (server && typeof server.listen === 'function') {
    server.listen({ onUnhandledRequest: 'warn' })
  }
})

afterEach(() => {
  cleanup()
  if (server && typeof server.resetHandlers === 'function') {
    server.resetHandlers()
  }
})

afterAll(() => {
  if (server && typeof server.close === 'function') {
    server.close()
  }
})

