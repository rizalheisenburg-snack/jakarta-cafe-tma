CREATE TABLE IF NOT EXISTS menu_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    price       INTEGER NOT NULL,
    category    TEXT    NOT NULL,
    emoji       TEXT    DEFAULT '☕',
    available   INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vouchers (
    code           TEXT    PRIMARY KEY,
    discount_type  TEXT    NOT NULL CHECK (discount_type IN ('percent', 'flat')),
    discount_value INTEGER NOT NULL,
    min_order      INTEGER DEFAULT 0,
    max_uses       INTEGER DEFAULT NULL,
    used_count     INTEGER DEFAULT 0,
    active         INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    username     TEXT,
    full_name    TEXT,
    status       TEXT    NOT NULL DEFAULT 'pending',
    subtotal     INTEGER NOT NULL,
    discount     INTEGER DEFAULT 0,
    total        INTEGER NOT NULL,
    voucher_code TEXT,
    note         TEXT,
    created_at   TEXT    DEFAULT (datetime('now','localtime')),
    updated_at   TEXT    DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id  INTEGER NOT NULL,
    item_id   INTEGER NOT NULL,
    item_name TEXT    NOT NULL,
    qty       INTEGER NOT NULL,
    price     INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
