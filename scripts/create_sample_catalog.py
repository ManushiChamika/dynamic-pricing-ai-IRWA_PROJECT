import csv
import os
from pathlib import Path

desktop_path = Path.home() / "Desktop"
output_file = desktop_path / "sample_catalog.csv"

sample_data = [
    {
        "sku": "LAPTOP-001",
        "title": "Dell XPS 15 Laptop",
        "currency": "USD",
        "current_price": 1299.99,
        "cost": 950.00,
        "stock": 15
    },
    {
        "sku": "LAPTOP-002",
        "title": "HP Pavilion 14",
        "currency": "USD",
        "current_price": 749.99,
        "cost": 550.00,
        "stock": 25
    },
    {
        "sku": "LAPTOP-003",
        "title": "Lenovo ThinkPad X1",
        "currency": "USD",
        "current_price": 1499.99,
        "cost": 1100.00,
        "stock": 10
    },
    {
        "sku": "LAPTOP-004",
        "title": "ASUS ROG Gaming Laptop",
        "currency": "USD",
        "current_price": 1899.99,
        "cost": 1400.00,
        "stock": 8
    },
    {
        "sku": "LAPTOP-005",
        "title": "Acer Aspire 5",
        "currency": "USD",
        "current_price": 599.99,
        "cost": 450.00,
        "stock": 30
    },
    {
        "sku": "MOUSE-001",
        "title": "Logitech MX Master 3",
        "currency": "USD",
        "current_price": 99.99,
        "cost": 70.00,
        "stock": 50
    },
    {
        "sku": "KEYBOARD-001",
        "title": "Corsair K95 RGB Mechanical",
        "currency": "USD",
        "current_price": 199.99,
        "cost": 140.00,
        "stock": 20
    },
    {
        "sku": "MONITOR-001",
        "title": "Dell UltraSharp 27 4K",
        "currency": "USD",
        "current_price": 649.99,
        "cost": 480.00,
        "stock": 12
    },
    {
        "sku": "HEADSET-001",
        "title": "Sony WH-1000XM4",
        "currency": "USD",
        "current_price": 349.99,
        "cost": 250.00,
        "stock": 35
    },
    {
        "sku": "WEBCAM-001",
        "title": "Logitech C920 HD Pro",
        "currency": "USD",
        "current_price": 79.99,
        "cost": 55.00,
        "stock": 45
    }
]

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['sku', 'title', 'currency', 'current_price', 'cost', 'stock']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(sample_data)

print(f"Sample catalog file created successfully at: {output_file}")
print(f"\nFile contains {len(sample_data)} sample products")
print("\nRequired columns:")
print("  - sku: Unique product ID")
print("  - title: Product name")
print("  - currency: e.g., USD, EUR")
print("  - current_price: Current price (must be non-negative)")
print("  - cost: Product cost (must be non-negative)")
print("  - stock: Available quantity (must be non-negative integer)")
