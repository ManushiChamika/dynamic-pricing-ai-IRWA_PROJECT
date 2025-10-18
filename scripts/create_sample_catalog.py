import csv
import os
from pathlib import Path

desktop_path = Path.home() / "Desktop"
output_file = desktop_path / "sample_catalog.csv"

sample_data = [
    {
        "sku": "LAPTOP-DELL-XPS-13-9350",
        "title": "Dell XPS 13 9350 Laptop",
        "currency": "USD",
        "current_price": 1199.99,
        "cost": 875.00,
        "stock": 15
    },
    {
        "sku": "LAPTOP-DELL-XPS-14-9440",
        "title": "Dell XPS 14 9440 Laptop",
        "currency": "USD",
        "current_price": 1449.99,
        "cost": 1060.00,
        "stock": 12
    },
    {
        "sku": "LAPTOP-DELL-PREMIUM-16",
        "title": "Dell 16 Premium Laptop",
        "currency": "USD",
        "current_price": 1799.99,
        "cost": 1315.00,
        "stock": 8
    },
    {
        "sku": "LAPTOP-LENOVO-THINKPAD-X1",
        "title": "Lenovo ThinkPad X1 Carbon",
        "currency": "USD",
        "current_price": 1499.99,
        "cost": 1095.00,
        "stock": 10
    },
    {
        "sku": "MOUSE-LOGITECH-MX-MASTER-4",
        "title": "Logitech MX Master 4 Wireless Mouse",
        "currency": "USD",
        "current_price": 119.99,
        "cost": 85.00,
        "stock": 50
    },
    {
        "sku": "MOUSE-LOGITECH-LIFT",
        "title": "Logitech LIFT Vertical Ergonomic Mouse",
        "currency": "USD",
        "current_price": 69.99,
        "cost": 50.00,
        "stock": 40
    },
    {
        "sku": "MOUSE-LOGITECH-M720",
        "title": "Logitech M720 Triathlon Multi-Device Wireless Mouse",
        "currency": "USD",
        "current_price": 44.99,
        "cost": 32.00,
        "stock": 60
    },
    {
        "sku": "MOUSE-LOGITECH-MX-ANYWHERE-3S",
        "title": "Logitech MX Anywhere 3S Compact Performance Mouse",
        "currency": "USD",
        "current_price": 79.99,
        "cost": 58.00,
        "stock": 35
    },
    {
        "sku": "MOUSE-LOGITECH-MX-VERTICAL",
        "title": "Logitech MX Vertical Advanced Ergonomic Mouse",
        "currency": "USD",
        "current_price": 109.99,
        "cost": 80.00,
        "stock": 25
    },
    {
        "sku": "MOUSE-LOGITECH-ERGO-M575S",
        "title": "Logitech ERGO M575S Wireless Trackball",
        "currency": "USD",
        "current_price": 39.99,
        "cost": 29.00,
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
