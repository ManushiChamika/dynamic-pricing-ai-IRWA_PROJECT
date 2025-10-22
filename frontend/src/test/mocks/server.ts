let server: any

export async function getServer() {
  if (server) return server

  // Prefer Node setup when running in Node or Node-like test envs
  if (typeof process !== 'undefined' && process.versions && process.versions.node) {
    const { setupServer } = await import('msw/node')
    const mswModule: any = await import('msw')
    const http = mswModule.http ?? mswModule.default?.http
    const { getHandlers } = await import('./handlers')
    const handlers = getHandlers(http)
    server = setupServer(...handlers)
  } else if (typeof window === 'undefined') {
    const { setupServer } = await import('msw/node')
    const mswModule: any = await import('msw')
    const http = mswModule.http ?? mswModule.default?.http
    const { getHandlers } = await import('./handlers')
    const handlers = getHandlers(http)
    server = setupServer(...handlers)
  } else {
    const { setupWorker } = await import('msw')
    const mswModule: any = await import('msw')
    const http = mswModule.http ?? mswModule.default?.http
    const { getHandlers } = await import('./handlers')
    const handlers = getHandlers(http)
    server = setupWorker(...handlers)
  }


  return server
}
