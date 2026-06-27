"""Run once to populate menu and sample vouchers."""
from db import get_conn, init_db

MENU = [
    # (name, description, price, category, emoji)
    ("Kopi Hitam", "Robusta lokal, pahit mantap", 12_000, "Kopi", "☕"),
    ("Kopi Susu", "Espresso + susu segar", 18_000, "Kopi", "🥛"),
    ("Es Kopi Gula Aren", "Cold brew + gula aren Banten", 22_000, "Kopi", "🧋"),
    ("Cappuccino", "Double shot + foam lembut", 25_000, "Kopi", "☕"),
    ("Matcha Latte", "Matcha Uji + oat milk", 28_000, "Non-Kopi", "🍵"),
    ("Es Teh Lemon", "Teh hitam + jeruk segar", 15_000, "Non-Kopi", "🍋"),
    ("Cokelat Panas", "Dark cocoa premium", 20_000, "Non-Kopi", "🍫"),
    ("Croissant", "Butter croissant fresh oven", 22_000, "Makanan", "🥐"),
    ("Roti Bakar Selai", "Roti sourdough + selai homemade", 18_000, "Makanan", "🍞"),
    ("Nasi Goreng Cafe", "Nasi goreng telur + ayam", 35_000, "Makanan", "🍳"),
    ("Sandwich Ayam", "Chicken mayo + sayuran segar", 30_000, "Makanan", "🥪"),
    ("Cheesecake", "New York style, per slice", 32_000, "Dessert", "🍰"),
    ("Brownies", "Fudgy dark chocolate", 20_000, "Dessert", "🍫"),
]

VOUCHERS = [
    # (code, discount_type, discount_value, min_order, max_uses)
    ("SELAMAT10", "percent", 10, 30_000, None),
    ("DISKON20K",  "flat",   20_000, 50_000, 50),
    ("GRATIS5",   "percent",  5,      0,     None),
]

def seed():
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM menu_items")
        if cur.fetchone()[0] > 0:
            print("Menu sudah ada, skip seed.")
            return

        cur.executemany(
            "INSERT INTO menu_items (name, description, price, category, emoji) VALUES (?,?,?,?,?)",
            MENU,
        )
        cur.executemany(
            "INSERT OR IGNORE INTO vouchers (code, discount_type, discount_value, min_order, max_uses) VALUES (?,?,?,?,?)",
            VOUCHERS,
        )
        conn.commit()
    print(f"Seed selesai: {len(MENU)} item menu, {len(VOUCHERS)} voucher.")

if __name__ == "__main__":
    seed()
