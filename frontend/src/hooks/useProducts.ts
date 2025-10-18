import { useEffect, useState } from 'react'
import { useAuthToken } from '../stores/authStore'

export function useProducts() {
  const [products, setProducts] = useState<string[]>([])
  const token = useAuthToken()

  const fetchProducts = async () => {
    if (!token) return
    try {
      const response = await fetch(`/api/catalog/products?token=${token}`)
      if (!response.ok) throw new Error('Failed to fetch products')
      const data = await response.json()
      const skus = data.products.map((p: any) => p.sku)
      setProducts(skus)
    } catch (err) {
      console.error('Error fetching products:', err)
    }
  }

  useEffect(() => {
    fetchProducts()
    const interval = setInterval(fetchProducts, 30000)
    return () => clearInterval(interval)
  }, [token])

  useEffect(() => {
    const handleCatalogUpdate = () => {
      fetchProducts()
    }
    window.addEventListener('catalog-updated', handleCatalogUpdate)
    return () => window.removeEventListener('catalog-updated', handleCatalogUpdate)
  }, [token])

  return { products, refetch: fetchProducts }
}
