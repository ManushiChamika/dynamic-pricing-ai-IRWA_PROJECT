import { rest } from 'msw'

export const handlers = [
  rest.get('/api/products/:sku', (req, res, ctx) => {
    const { sku } = req.params
    return res(
      ctx.status(200),
      ctx.json({ sku, price: 123.45, title: `Mock product ${sku}` })
    )
  }),
]
