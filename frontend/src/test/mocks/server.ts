import { handlers } from './handlers'

let server: any

if (typeof window === 'undefined') {
  // Node environment (Vitest)
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { setupServer } = require('msw/node')
  server = setupServer(...handlers)
}

export { server }
