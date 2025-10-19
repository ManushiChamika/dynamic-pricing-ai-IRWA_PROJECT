import sqlite3
from pathlib import Path

product_urls = {
    "LAPTOP-001": "https://www.amazon.com/Dell-XPS-15-9530-Laptop/dp/B0C5RZQQFK",
    "LAPTOP-002": "https://www.amazon.com/HP-Pavilion-Laptop-Graphics-15-eg3097nr/dp/B0CXGZFN3M",
    "LAPTOP-003": "https://www.amazon.com/Lenovo-ThinkPad-X1-Carbon-Gen/dp/B0C4N6NQYT",
    "MOUSE-001": "https://www.amazon.com/Logitech-MX-Master-3S-Wireless/dp/B09HM94VDS",
    "MONITOR-001": "https://www.amazon.com/Dell-UltraSharp-U2723DE-USB-C-Monitor/dp/B09TQMQNS8",
    "KEYBOARD-001": "https://www.amazon.com/Logitech-Wireless-Keyboard-Windows-Computer/dp/B07S92QBCF",
    "HEADSET-001": "https://www.amazon.com/HyperX-Cloud-II-Gaming-Headset/dp/B00SAYCXWG",
    "WEBCAM-001": "https://www.amazon.com/Logitech-Desktop-Widescreen-Calling-Recording/dp/B006JH8T3S"
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
