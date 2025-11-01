from locust import HttpUser, task, between


class PricingUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def get_product(self):
        self.client.get('/api/products/TEST-SKU')

    @task(1)
    def get_price_proposal(self):
        self.client.post('/api/price/propose', json={'sku': 'TEST-SKU', 'our_price': 100.0})
