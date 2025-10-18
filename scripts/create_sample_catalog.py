import csv
import os
from pathlib import Path

desktop_path = Path.home() / "Desktop"
output_file = desktop_path / "sample_catalog.csv"

sample_data = [
    {
        "sku": "LAPTOP-APPLE-MACBOOK-AIR-M3",
        "title": "Apple MacBook Air 13-inch M3",
        "currency": "USD",
        "current_price": 1099.00,
        "cost": 820.00,
        "stock": 18
    },
    {
        "sku": "LAPTOP-APPLE-MACBOOK-PRO-14-M3",
        "title": "Apple MacBook Pro 14-inch M3",
        "currency": "USD",
        "current_price": 1599.00,
        "cost": 1200.00,
        "stock": 12
    },
    {
        "sku": "LAPTOP-DELL-XPS-13-PLUS",
        "title": "Dell XPS 13 Plus",
        "currency": "USD",
        "current_price": 1299.00,
        "cost": 950.00,
        "stock": 15
    },
    {
        "sku": "LAPTOP-HP-SPECTRE-X360",
        "title": "HP Spectre x360 14",
        "currency": "USD",
        "current_price": 1399.00,
        "cost": 1020.00,
        "stock": 10
    },
    {
        "sku": "LAPTOP-LENOVO-THINKPAD-X1-CARBON-GEN11",
        "title": "Lenovo ThinkPad X1 Carbon Gen 11",
        "currency": "USD",
        "current_price": 1449.00,
        "cost": 1060.00,
        "stock": 14
    },
    {
        "sku": "PHONE-APPLE-IPHONE-15-PRO",
        "title": "Apple iPhone 15 Pro 128GB",
        "currency": "USD",
        "current_price": 999.00,
        "cost": 550.00,
        "stock": 25
    },
    {
        "sku": "PHONE-SAMSUNG-GALAXY-S24-ULTRA",
        "title": "Samsung Galaxy S24 Ultra 256GB",
        "currency": "USD",
        "current_price": 1199.99,
        "cost": 680.00,
        "stock": 20
    },
    {
        "sku": "PHONE-GOOGLE-PIXEL-8-PRO",
        "title": "Google Pixel 8 Pro 128GB",
        "currency": "USD",
        "current_price": 999.00,
        "cost": 580.00,
        "stock": 18
    },
    {
        "sku": "TABLET-APPLE-IPAD-PRO-11",
        "title": "Apple iPad Pro 11-inch M4",
        "currency": "USD",
        "current_price": 999.00,
        "cost": 650.00,
        "stock": 22
    },
    {
        "sku": "TABLET-SAMSUNG-GALAXY-TAB-S9",
        "title": "Samsung Galaxy Tab S9",
        "currency": "USD",
        "current_price": 799.99,
        "cost": 480.00,
        "stock": 16
    },
    {
        "sku": "HEADPHONES-SONY-WH1000XM5",
        "title": "Sony WH-1000XM5 Wireless Noise Cancelling",
        "currency": "USD",
        "current_price": 399.99,
        "cost": 220.00,
        "stock": 35
    },
    {
        "sku": "HEADPHONES-APPLE-AIRPODS-PRO-2",
        "title": "Apple AirPods Pro 2nd Generation",
        "currency": "USD",
        "current_price": 249.00,
        "cost": 140.00,
        "stock": 50
    },
    {
        "sku": "HEADPHONES-BOSE-QC45",
        "title": "Bose QuietComfort 45 Wireless",
        "currency": "USD",
        "current_price": 329.00,
        "cost": 180.00,
        "stock": 28
    },
    {
        "sku": "WATCH-APPLE-WATCH-SERIES-9",
        "title": "Apple Watch Series 9 GPS 45mm",
        "currency": "USD",
        "current_price": 429.00,
        "cost": 260.00,
        "stock": 32
    },
    {
        "sku": "WATCH-SAMSUNG-GALAXY-WATCH-6",
        "title": "Samsung Galaxy Watch 6 Classic 47mm",
        "currency": "USD",
        "current_price": 399.99,
        "cost": 230.00,
        "stock": 24
    },
    {
        "sku": "MOUSE-LOGITECH-MX-MASTER-3S",
        "title": "Logitech MX Master 3S Wireless Mouse",
        "currency": "USD",
        "current_price": 99.99,
        "cost": 65.00,
        "stock": 45
    },
    {
        "sku": "KEYBOARD-LOGITECH-MX-KEYS",
        "title": "Logitech MX Keys Advanced Wireless Keyboard",
        "currency": "USD",
        "current_price": 119.99,
        "cost": 75.00,
        "stock": 38
    },
    {
        "sku": "MONITOR-DELL-ULTRASHARP-27-4K",
        "title": "Dell UltraSharp 27 4K USB-C Monitor U2723DE",
        "currency": "USD",
        "current_price": 549.99,
        "cost": 350.00,
        "stock": 12
    },
    {
        "sku": "MONITOR-LG-ULTRAFINE-5K",
        "title": "LG UltraFine 27 5K Display",
        "currency": "USD",
        "current_price": 1299.99,
        "cost": 820.00,
        "stock": 8
    },
    {
        "sku": "CONSOLE-SONY-PS5",
        "title": "Sony PlayStation 5 Console",
        "currency": "USD",
        "current_price": 499.99,
        "cost": 380.00,
        "stock": 20
    },
    {
        "sku": "CONSOLE-MICROSOFT-XBOX-SERIES-X",
        "title": "Microsoft Xbox Series X",
        "currency": "USD",
        "current_price": 499.99,
        "cost": 375.00,
        "stock": 18
    },
    {
        "sku": "CONSOLE-NINTENDO-SWITCH-OLED",
        "title": "Nintendo Switch OLED Model",
        "currency": "USD",
        "current_price": 349.99,
        "cost": 260.00,
        "stock": 25
    },
    {
        "sku": "CAMERA-SONY-A7IV",
        "title": "Sony Alpha a7 IV Mirrorless Camera Body",
        "currency": "USD",
        "current_price": 2498.00,
        "cost": 1850.00,
        "stock": 6
    },
    {
        "sku": "CAMERA-CANON-EOS-R6-MARKII",
        "title": "Canon EOS R6 Mark II Mirrorless Camera Body",
        "currency": "USD",
        "current_price": 2499.00,
        "cost": 1860.00,
        "stock": 5
    },
    {
        "sku": "SPEAKER-SONOS-ERA-300",
        "title": "Sonos Era 300 Smart Speaker",
        "currency": "USD",
        "current_price": 449.00,
        "cost": 280.00,
        "stock": 22
    },
    {
        "sku": "SPEAKER-APPLE-HOMEPOD-2",
        "title": "Apple HomePod 2nd Generation",
        "currency": "USD",
        "current_price": 299.00,
        "cost": 180.00,
        "stock": 30
    },
    {
        "sku": "ROUTER-NETGEAR-NIGHTHAWK-AX12",
        "title": "Netgear Nighthawk AX12 12-Stream WiFi 6 Router",
        "currency": "USD",
        "current_price": 449.99,
        "cost": 290.00,
        "stock": 15
    },
    {
        "sku": "SSD-SAMSUNG-990-PRO-2TB",
        "title": "Samsung 990 PRO 2TB PCIe 4.0 NVMe SSD",
        "currency": "USD",
        "current_price": 179.99,
        "cost": 115.00,
        "stock": 40
    },
    {
        "sku": "SSD-CRUCIAL-P5-PLUS-1TB",
        "title": "Crucial P5 Plus 1TB PCIe 4.0 NVMe SSD",
        "currency": "USD",
        "current_price": 89.99,
        "cost": 58.00,
        "stock": 55
    },
    {
        "sku": "PRINTER-HP-LASERJET-PRO-M404DN",
        "title": "HP LaserJet Pro M404dn Printer",
        "currency": "USD",
        "current_price": 329.00,
        "cost": 210.00,
        "stock": 12
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
