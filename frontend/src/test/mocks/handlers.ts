export function getHandlers(http: any) {
  return [
    http.get('*', (req: any, res: any, ctx: any) => {
      try {
        const pathname = req.url && req.url.pathname ? req.url.pathname : new URL(req.url).pathname
        if (pathname === '/api/catalog/products') {
          return res(
            ctx.status(200),
            ctx.json({ products: [{ sku: 'SKU123' }, { sku: 'SKU456' }] })
          )
        }
      } catch {
        // Ignore URL parsing errors
      }
      return res(ctx.status(404))
    }),
    http.get('/api/products/:sku', (req: any, res: any, ctx: any) => {
      const { sku } = req.params
      return res(ctx.status(200), ctx.json({ sku, price: 123.45, title: `Mock product ${sku}` }))
    }),
  ]
}
