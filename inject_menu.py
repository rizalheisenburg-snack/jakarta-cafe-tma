"""Inject/replace menu dengan daftar menu restoran baru. Aman dijalanin ulang."""
from db import get_conn, init_db

IMG = "?w=400&q=80"

# ── URL gambar per jenis makanan ──────────────────────────────────────────────
_NOODLE_SOUP = [
    f"https://images.unsplash.com/photo-1680675706515-fb3eb73116d4{IMG}",
    f"https://images.unsplash.com/photo-1644083130607-b5ecc6cc7e8e{IMG}",
    f"https://images.unsplash.com/photo-1644083152667-2c78739e882a{IMG}",
    f"https://images.unsplash.com/photo-1612927601601-6638404737ce{IMG}",
    f"https://images.unsplash.com/photo-1698327097684-5726266fc2d4{IMG}",
]
_DUMPLING = [
    f"https://images.unsplash.com/photo-1541696432-82c6da8ce7bf{IMG}",
    f"https://images.unsplash.com/photo-1639119419756-d909653abbdd{IMG}",
    f"https://images.unsplash.com/photo-1619528395522-997915c3b518{IMG}",
    f"https://images.unsplash.com/photo-1780375578522-6d75c6932b6b{IMG}",
    f"https://images.unsplash.com/photo-1781332147547-1f0edb2a78a4{IMG}",
]
_FRIED_NOODLE = [
    f"https://images.unsplash.com/photo-1612929633738-8fe44f7ec841{IMG}",
    f"https://images.unsplash.com/photo-1585032226651-759b368d7246{IMG}",
    f"https://images.unsplash.com/photo-1607328874071-45a9cd600644{IMG}",
    f"https://images.unsplash.com/photo-1553621043-f607bfbf6640{IMG}",
    f"https://images.unsplash.com/photo-1634864572865-1cf8ff8bd23d{IMG}",
]
_FRIED_RICE = [
    f"https://images.unsplash.com/photo-1680674774705-90b4904b3a7f{IMG}",
    f"https://images.unsplash.com/photo-1647093953000-9065ed6f85ef{IMG}",
    f"https://images.unsplash.com/photo-1603133872878-684f208fb84b{IMG}",
    f"https://images.unsplash.com/photo-1609570324378-ec0c4c9b6ba8{IMG}",
]
_RICE_SOUP = [
    f"https://images.unsplash.com/photo-1665593998976-d957f2827fe7{IMG}",
    f"https://images.unsplash.com/photo-1621658537360-dfcb008fe19f{IMG}",
    f"https://images.unsplash.com/photo-1590133377962-a18b71fd78ea{IMG}",
    f"https://images.unsplash.com/photo-1645530655296-6eb45b85e3da{IMG}",
]
_CHICKEN_RICE = [
    f"https://images.unsplash.com/photo-1569058242252-623df46b5025{IMG}",
    f"https://images.unsplash.com/photo-1603496987674-79600a000f55{IMG}",
    f"https://images.unsplash.com/photo-1589302168068-964664d93dc0{IMG}",
    f"https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a{IMG}",
]
_GEPREK = [
    f"https://images.unsplash.com/photo-1672856399675-8c099efbe0e2{IMG}",
    f"https://images.unsplash.com/photo-1599354607460-d121f1402a59{IMG}",
    f"https://images.unsplash.com/photo-1569058242252-623df46b5025{IMG}",
    f"https://images.unsplash.com/photo-1647093953000-9065ed6f85ef{IMG}",
]
_BENTO = [
    f"https://images.unsplash.com/photo-1696677049263-cc38af1c7681{IMG}",
    f"https://images.unsplash.com/photo-1543352632-5a4b24e4d2a6{IMG}",
    f"https://images.unsplash.com/photo-1616645258469-ec681c17f3ee{IMG}",
    f"https://images.unsplash.com/photo-1558689509-900d3d3cc727{IMG}",
    f"https://images.unsplash.com/photo-1543353071-c953d88f7033{IMG}",
]
_DIMSUM = [
    f"https://images.unsplash.com/photo-1707013533606-62919aa3aa29{IMG}",
    f"https://images.unsplash.com/photo-1563245372-f21724e3856d{IMG}",
    f"https://images.unsplash.com/photo-1517499414974-3b42addf2d86{IMG}",
]
_EXTRA = f"https://images.unsplash.com/photo-1536304993881-ff86e0c9c4cb{IMG}"

def _n(lst, i): return lst[i % len(lst)]

# ── MENU: (name, description, price, category, emoji, image_url) ──────────────
MENU = [
    # Bakmie & Yam ─────────────────────────────────────────────────────────────
    ("Bakmie Ayam",               "鸡肉面", 12_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,0)),
    ("Bakmie Ayam Jumbo",         "鸡肉面", 15_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,1)),
    ("Bakmie Ayam Pangsit",       "鸡肉面", 16_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,2)),
    ("Bakmie Ayam Pangsit Jumbo", "鸡肉面", 19_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,3)),
    ("Kwetiau Yam",               "煮粿条", 12_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,4)),
    ("Kwetiau Yam Jumbo",         "煮粿条", 15_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,0)),
    ("Kwetiau Yam Pangsit",       "煮粿条", 16_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,1)),
    ("Kwetiau Yam Pangsit Jumbo", "煮粿条", 19_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,2)),
    ("Bihun Yam",                 "煮米粉", 12_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,3)),
    ("Bihun Yam Jumbo",           "煮米粉", 15_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,4)),
    ("Bihun Yam Pangsit",         "煮米粉", 16_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,0)),
    ("Bihun Yam Pangsit Jumbo",   "煮米粉", 19_000, "Bakmie & Yam", "🍜", _n(_NOODLE_SOUP,1)),

    # Wonton ───────────────────────────────────────────────────────────────────
    ("Pangsit/Wonton Ayam (Soup)",    "水饺",     12_000, "Wonton", "🥟", _n(_DUMPLING,0)),
    ("Pangsit/Wonton Yam Ayam (dry)", "水饺",     12_000, "Wonton", "🥟", _n(_DUMPLING,1)),
    ("Chicken Dumpling",              "水饺",     14_000, "Wonton", "🥟", _n(_DUMPLING,2)),
    ("Pangsit/Wonton (rebus)",        "Per buah",  2_000, "Wonton", "🥟", _n(_DUMPLING,3)),
    ("Pangsit Goreng",                "Per buah",    500, "Wonton", "🥟", _n(_DUMPLING,4)),

    # Goreng ───────────────────────────────────────────────────────────────────
    ("Mie Goreng",                    "炒面",  12_000, "Goreng", "🍳", _n(_FRIED_NOODLE,0)),
    ("Mie Goreng Jumbo",              "炒面",  15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,1)),
    ("Mie Goreng + Telur",            "炒面",  15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,2)),
    ("Mie Goreng Jumbo + Telur",      "炒面",  18_000, "Goreng", "🍳", _n(_FRIED_NOODLE,3)),
    ("Bihun Goreng",                  "炒米粉", 12_000, "Goreng", "🍳", _n(_FRIED_NOODLE,4)),
    ("Bihun Goreng Jumbo",            "炒米粉", 15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,0)),
    ("Bihun Goreng + Telur",          "炒米粉", 15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,1)),
    ("Bihun Goreng Jumbo + Telur",    "炒米粉", 18_000, "Goreng", "🍳", _n(_FRIED_NOODLE,2)),
    ("Kwetiau Goreng",                "炒粿条", 12_000, "Goreng", "🍳", _n(_FRIED_NOODLE,3)),
    ("Kwetiau Goreng Jumbo",          "炒粿条", 15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,4)),
    ("Kwetiau Goreng + Telur",        "炒粿条", 15_000, "Goreng", "🍳", _n(_FRIED_NOODLE,0)),
    ("Kwetiau Goreng Jumbo + Telur",  "炒粿条", 18_000, "Goreng", "🍳", _n(_FRIED_NOODLE,1)),
    ("Nasi Goreng Bakso",             "肉丸炒饭",10_000, "Goreng", "🍳", _n(_FRIED_RICE,0)),
    ("Nasi Goreng Bakso + Telur",     "肉丸炒饭",13_000, "Goreng", "🍳", _n(_FRIED_RICE,1)),
    ("Nasi Goreng Bakso Jumbo",       "肉丸炒饭",15_000, "Goreng", "🍳", _n(_FRIED_RICE,2)),
    ("Nasi Goreng Bakso Jumbo + Telur","肉丸炒饭",18_000,"Goreng", "🍳", _n(_FRIED_RICE,3)),
    ("Nasi Goreng Teri",              "",       14_000, "Goreng", "🍳", _n(_FRIED_RICE,0)),
    ("Nasi Goreng Teri Jumbo",        "",       17_000, "Goreng", "🍳", _n(_FRIED_RICE,1)),
    ("Nasi Goreng Teri + Telur",      "",       17_000, "Goreng", "🍳", _n(_FRIED_RICE,2)),
    ("Nasi Goreng Teri Jumbo + Telur","",       20_000, "Goreng", "🍳", _n(_FRIED_RICE,3)),
    ("Nasi Liwet Ikan",               "",       15_000, "Goreng", "🍚", _n(_RICE_SOUP,0)),
    ("Nasi Liwet Ikan Asin",          "",       14_000, "Goreng", "🍚", _n(_RICE_SOUP,1)),
    ("Nasi Liwet Ayam",               "",       14_000, "Goreng", "🍚", _n(_RICE_SOUP,2)),

    # Nasi Soup ────────────────────────────────────────────────────────────────
    ("N. Soto Daging",          "肉汤",      14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,0)),
    ("N. Soto Tangkar",         "",          14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,1)),
    ("N. Pangsit Ayam (Soup)",  "水饺",      14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,2)),
    ("N. Kari Ayam",            "",          14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,3)),
    ("N. Tim (Soup)",           "蒸米饭",    12_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,0)),
    ("N. Cilok Sapi (Soup)",    "鸡肉牛肉丸",14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,1)),
    ("Cilok Sapi (Soup)",       "鸡肉牛肉丸",12_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,2)),
    ("N. Sop Ayam Kampung",     "",          14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,3)),
    ("N. Sop Daging",           "",          14_000, "Nasi Soup", "🍲", _n(_RICE_SOUP,0)),

    # Nasi Ayam ────────────────────────────────────────────────────────────────
    ("N. Ayam Goreng (paha)",       "", 14_000, "Nasi Ayam", "🍗", _n(_CHICKEN_RICE,0)),
    ("N. Ayam Goreng Paha (Negri)", "", 12_000, "Nasi Ayam", "🍗", _n(_CHICKEN_RICE,1)),
    ("N. Ayam Goreng (dada)",       "", 14_000, "Nasi Ayam", "🍗", _n(_CHICKEN_RICE,2)),
    ("N. Ayam Bakar (Paha)",        "", 12_000, "Nasi Ayam", "🍗", _n(_CHICKEN_RICE,3)),
    ("N. Nugget 5pcs",              "", 12_000, "Nasi Ayam", "🍗", _n(_CHICKEN_RICE,0)),
    ("N. Telur Dadar Nugget 3pcs",  "", 12_000, "Nasi Ayam", "🍳", _n(_CHICKEN_RICE,1)),
    ("N. Telur Ceplok Nugget 3pcs", "", 12_000, "Nasi Ayam", "🍳", _n(_CHICKEN_RICE,2)),
    ("N. Ikan Saba Telur Ceplok",   "", 15_000, "Nasi Ayam", "🐟", _n(_CHICKEN_RICE,3)),
    ("N. Ikan Saba Filet",          "", 15_000, "Nasi Ayam", "🐟", _n(_CHICKEN_RICE,0)),
    ("N. Cumi Penyet",              "", 17_000, "Nasi Ayam", "🦑", _n(_CHICKEN_RICE,1)),
    ("N. Udang Penyet",             "", 17_000, "Nasi Ayam", "🦐", _n(_CHICKEN_RICE,2)),
    ("N. Udang Cumi Penyet",        "", 20_000, "Nasi Ayam", "🦐", _n(_CHICKEN_RICE,3)),
    ("N. 2 Telur Dadar (bawang)",   "", 10_000, "Nasi Ayam", "🍳", _n(_CHICKEN_RICE,0)),
    ("N. 2 Telur Ceplok (kecap)",   "", 10_000, "Nasi Ayam", "🍳", _n(_CHICKEN_RICE,1)),

    # Nasi Geprek ──────────────────────────────────────────────────────────────
    ("N. Teri Dadar Geprek",        "", 15_000, "Nasi Geprek", "🌶️", _n(_GEPREK,0)),
    ("N. Ikan Teri Nugget 2pcs",    "", 16_000, "Nasi Geprek", "🌶️", _n(_GEPREK,1)),
    ("N. Ikan Teri Geprek",         "", 12_000, "Nasi Geprek", "🌶️", _n(_GEPREK,2)),
    ("N. Ayam Geprek (paha)",       "", 14_000, "Nasi Geprek", "🌶️", _n(_GEPREK,3)),
    ("N. Ayam Geprek (dada)",       "", 14_000, "Nasi Geprek", "🌶️", _n(_GEPREK,0)),
    ("N. Nugget Geprek 5pcs",       "", 12_000, "Nasi Geprek", "🌶️", _n(_GEPREK,1)),
    ("N. Ayam Geprek + Nugget 2pcs","", 18_000, "Nasi Geprek", "🌶️", _n(_GEPREK,2)),
    ("N. Dadar Nugget Geprek 3pcs", "", 12_000, "Nasi Geprek", "🌶️", _n(_GEPREK,3)),
    ("N. Ceplok Nugget Geprek 3pcs","", 12_000, "Nasi Geprek", "🌶️", _n(_GEPREK,0)),
    ("N. 2 Telur Dadar (Geprek)",   "", 10_000, "Nasi Geprek", "🌶️", _n(_GEPREK,1)),

    # Bento & Bowl ─────────────────────────────────────────────────────────────
    ("N. Bento A",            "", 20_000, "Bento & Bowl", "🍱", _n(_BENTO,0)),
    ("N. Bento B",            "", 16_000, "Bento & Bowl", "🍱", _n(_BENTO,1)),
    ("N. Bento C",            "", 16_000, "Bento & Bowl", "🍱", _n(_BENTO,2)),
    ("N. Bento D",            "", 16_000, "Bento & Bowl", "🍱", _n(_BENTO,3)),
    ("N. Beef Bowl",          "", 20_000, "Bento & Bowl", "🥩", _n(_BENTO,4)),
    ("N. Sayap Ati Ampla",    "", 14_000, "Bento & Bowl", "🍗", _n(_BENTO,0)),
    ("N. Babat",              "", 16_000, "Bento & Bowl", "🍖", _n(_BENTO,1)),
    ("Chicken Wing",          "",  4_000, "Bento & Bowl", "🍗", _n(_BENTO,2)),
    ("Ikan Teri ½ Porsi",     "",  4_000, "Bento & Bowl", "🐟", _n(_BENTO,3)),
    ("Ikan Teri 1 Porsi",     "",  8_000, "Bento & Bowl", "🐟", _n(_BENTO,4)),

    # Pelengkap ────────────────────────────────────────────────────────────────
    ("Nasi Putih",             "白米", 2_000, "Pelengkap", "🍚", _EXTRA),
    ("Telur Rebus",            "蛋",   2_000, "Pelengkap", "🥚", _EXTRA),
    ("Telur Dadar/Ceplok Satuan","",   3_000, "Pelengkap", "🍳", _EXTRA),
    ("Nugget Satuan",          "",     2_000, "Pelengkap", "🍗", _EXTRA),
    ("Bakso Sapi Satuan",      "",     2_000, "Pelengkap", "🍢", _EXTRA),
    ("Bakso Ikan Satuan",      "",     1_000, "Pelengkap", "🍢", _EXTRA),

    # Snacks ───────────────────────────────────────────────────────────────────
    ("Choipan/Chaikue Bangkuang", "菜盘", 12_000, "Snacks", "🥟", _n(_DIMSUM,0)),
]


def inject():
    init_db()
    with get_conn() as conn:
        cur = conn.cursor()
        # Tambah kolom image_url kalau belum ada
        cols = [r[1] for r in cur.execute("PRAGMA table_info(menu_items)").fetchall()]
        if "image_url" not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN image_url TEXT")

        cur.execute("DELETE FROM menu_items")
        cur.executemany(
            "INSERT INTO menu_items (name, description, price, category, emoji, image_url) VALUES (?,?,?,?,?,?)",
            MENU,
        )
        conn.commit()
    print(f"Inject selesai: {len(MENU)} item menu.")


if __name__ == "__main__":
    inject()
