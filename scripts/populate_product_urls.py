import sqlite3
from pathlib import Path

product_urls = {
    "LAPTOP-APPLE-MACBOOK-AIR-M3": "https://www.amazon.com/Apple-2024-MacBook-13-inch-Laptop/dp/B0CX23GFMJ",
    "LAPTOP-APPLE-MACBOOK-PRO-14-M3": "https://www.amazon.com/Apple-MacBook-Laptop-8%E2%80%91core-10%E2%80%91core/dp/B0CM5JV268",
    "LAPTOP-DELL-XPS-13-PLUS": "https://www.amazon.com/Dell-XPS-Plus-9320-Laptop/dp/B0B8R74VYB",
    "LAPTOP-HP-SPECTRE-X360": "https://www.amazon.com/HP-Spectre-2-8K-Touch-Screen/dp/B0BXJ9CZ3V",
    "LAPTOP-LENOVO-THINKPAD-X1-CARBON-GEN11": "https://www.amazon.com/Lenovo-ThinkPad-Carbon-Gen-Laptop/dp/B0C4N6NQYT",
    "PHONE-APPLE-IPHONE-15-PRO": "https://www.amazon.com/Apple-iPhone-15-Pro-128/dp/B0CHTJ1BNQ",
    "PHONE-SAMSUNG-GALAXY-S24-ULTRA": "https://www.amazon.com/SAMSUNG-Factory-Unlocked-Smartphone-Titanium/dp/B0CMDRCZBJ",
    "PHONE-GOOGLE-PIXEL-8-PRO": "https://www.amazon.com/Google-Pixel-Pro-Smartphone-Telephoto/dp/B0CGT6ZN1T",
    "TABLET-APPLE-IPAD-PRO-11": "https://www.amazon.com/Apple-iPad-Pro-11-Inch-Landscape/dp/B0D3J9XDMQ",
    "TABLET-SAMSUNG-GALAXY-TAB-S9": "https://www.amazon.com/SAMSUNG-Android-Snapdragon-Processor-Graphite/dp/B0C39J87P9",
    "HEADPHONES-SONY-WH1000XM5": "https://www.amazon.com/Sony-WH-1000XM5-Canceling-Headphones-Hands-Free/dp/B09XS7JWHH",
    "HEADPHONES-APPLE-AIRPODS-PRO-2": "https://www.amazon.com/Apple-Generation-Cancelling-Transparency-Personalized/dp/B0CHWRXH8B",
    "HEADPHONES-BOSE-QC45": "https://www.amazon.com/Bose-QuietComfort-Bluetooth-Cancelling-Headphones/dp/B098FKXT8L",
    "WATCH-APPLE-WATCH-SERIES-9": "https://www.amazon.com/Apple-Watch-Smartwatch-Midnight-Aluminum/dp/B0CHX9CY7W",
    "WATCH-SAMSUNG-GALAXY-WATCH-6": "https://www.amazon.com/SAMSUNG-Bluetooth-Smartwatch-Monitoring-Resistant/dp/B0C79LY8C7",
    "MOUSE-LOGITECH-MX-MASTER-3S": "https://www.amazon.com/Logitech-MX-Master-3S-Wireless/dp/B09HM94VDS",
    "KEYBOARD-LOGITECH-MX-KEYS": "https://www.amazon.com/Logitech-Advanced-Wireless-Illuminated-Keyboard/dp/B07S92QBCF",
    "MONITOR-DELL-ULTRASHARP-27-4K": "https://www.amazon.com/Dell-UltraSharp-U2723DE-USB-C-Monitor/dp/B09TQMQNS8",
    "MONITOR-LG-ULTRAFINE-5K": "https://www.amazon.com/LG-27MD5KL-B-UltraFine-27-Inch-Thunderbolt/dp/B07XV9NQSJ",
    "CONSOLE-SONY-PS5": "https://www.amazon.com/PlayStation-5-Console/dp/B0CL61F39H",
    "CONSOLE-MICROSOFT-XBOX-SERIES-X": "https://www.amazon.com/Xbox-Series-X/dp/B08H75RTZ8",
    "CONSOLE-NINTENDO-SWITCH-OLED": "https://www.amazon.com/Nintendo-Switch-OLED-Model-White-Joy/dp/B098RKWHHZ"
}

def populate_urls():
    db_path = Path(__file__).parent.parent / "app" / "data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for sku, url in product_urls.items():
        cursor.execute("UPDATE product_catalog SET source_url = ? WHERE sku = ?", (url, sku))
        print(f"Updated {sku} with URL")
    
    conn.commit()
    
    cursor.execute("SELECT sku, title, source_url FROM product_catalog")
    rows = cursor.fetchall()
    print("\nProducts with URLs:")
    for row in rows:
        print(f"  {row[0]}: {row[1][:30]}... -> {row[2] or 'NO URL'}")
    
    conn.close()

if __name__ == "__main__":
    populate_urls()
