"""Run once untuk isi menu awal. Idempotent — aman dijalanin berkali-kali."""
from db import get_conn, init_db

# Harga dalam RIEL
MENU = [
    # (name, description, price, category, emoji)
    ("Kopi Hitam",        "Robusta lokal, pahit mantap",        4_000, "Kopi",     "☕"),
    ("Kopi Susu",         "Espresso + susu segar",              6_000, "Kopi",     "🥛"),
    ("Es Kopi Gula Aren", "Cold brew + gula aren",              8_000, "Kopi",     "🧋"),
    ("Cappuccino",        "Double shot + foam lembut",          9_000, "Kopi",     "☕"),
    ("Matcha Latte",      "Matcha Uji + oat milk",             10_000, "Non-Kopi", "🍵"),
    ("Es Teh Lemon",      "Teh hitam + jeruk segar",            5_000, "Non-Kopi", "🍋"),
    ("Cokelat Panas",     "Dark cocoa premium",                 7_000, "Non-Kopi", "🍫"),
    ("Croissant",         "Butter croissant fresh oven",        8_000, "Makanan",  "🥐"),
    ("Roti Bakar Selai",  "Roti sourdough + selai homemade",    6_000, "Makanan",  "🍞"),
    ("Nasi Goreng Cafe",  "Nasi goreng telur + ayam",          12_000, "Makanan",  "🍳"),
    ("Sandwich Ayam",     "Chicken mayo + sayuran segar",      11_000, "Makanan",  "🥪"),
    ("Cheesecake",        "New York style, per slice",         12_000, "Dessert",  "🍰"),
    ("Brownies",          "Fudgy dark chocolate",               7_000, "Dessert",  "🍫"),
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
        conn.commit()
    print(f"Seed selesai: {len(MENU)} item menu.")


if __name__ == "__main__":
    seed()
