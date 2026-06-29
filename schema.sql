-- Semua harga dalam RIEL (integer, ga ada desimal)

CREATE TABLE IF NOT EXISTS menu_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    price       INTEGER NOT NULL,          -- riel
    category    TEXT    NOT NULL,
    emoji       TEXT    DEFAULT '☕',
    image_url   TEXT,
    available   INTEGER DEFAULT 1          -- 1=ada, 0=habis
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    username       TEXT,
    full_name      TEXT,

    -- State dapur
    status         TEXT    NOT NULL DEFAULT 'PRE_CHECK',
    -- PRE_CHECK | PARTIAL_PENDING | PENDING | CONFIRMED | PREPARING | DONE
    -- | REJECTED | CANCELLED

    -- Payment (terpisah dari state dapur)
    payment_status TEXT    NOT NULL DEFAULT 'UNPAID',  -- UNPAID | PAID
    paid_currency  TEXT,                               -- 'RIEL' | 'USD' (apa yang masuk laci)
    paid_at        TEXT,                               -- UTC datetime, wajib UTC

    -- Voucher
    voucher_used   INTEGER DEFAULT 0,      -- 1 = voucher dipakai
    voucher_value  INTEGER DEFAULT 0,      -- riel yang dipotong voucher (maks 10000)

    -- Harga (GENERATED supaya ga bisa drift manual)
    subtotal       INTEGER NOT NULL,       -- sum(line_total) sebelum voucher
    discount       INTEGER GENERATED ALWAYS AS (voucher_value) STORED,
    total          INTEGER GENERATED ALWAYS AS (subtotal - voucher_value) STORED,

    note           TEXT,
    created_at     TEXT DEFAULT (datetime('now')),     -- UTC
    updated_at     TEXT DEFAULT (datetime('now'))      -- UTC
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    item_id    INTEGER NOT NULL,
    item_name  TEXT    NOT NULL,
    qty        INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,           -- riel, snapshot saat checkout
    line_total INTEGER GENERATED ALWAYS AS (qty * unit_price) STORED,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
