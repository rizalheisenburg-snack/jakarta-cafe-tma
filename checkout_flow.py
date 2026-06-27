"""Telegram initData verification + checkout logic."""
from __future__ import annotations
import hashlib
import hmac
import json
import time
import urllib.parse

from config import BOT_TOKEN
from db import get_conn
from state_machine import validate_voucher, consume_voucher


def verify_init_data(init_data: str, max_age_seconds: int = 3600) -> dict | None:
    """Return parsed user dict if initData is valid, else None."""
    params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        return None

    auth_date = int(params.get("auth_date", 0))
    if time.time() - auth_date > max_age_seconds:
        return None

    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        return None

    user_raw = params.get("user", "{}")
    return json.loads(user_raw)


def checkout(user: dict, items: list[dict], voucher_code: str | None, note: str) -> dict:
    """
    items: [{"item_id": int, "qty": int}, ...]
    Returns {"ok": True, "order_id": int} or {"ok": False, "error": str}
    """
    if not items:
        return {"ok": False, "error": "Keranjang kosong"}

    with get_conn() as conn:
        menu_rows = conn.execute("SELECT * FROM menu_items WHERE available=1").fetchall()
    menu_map = {r["id"]: dict(r) for r in menu_rows}

    order_items = []
    subtotal = 0
    for entry in items:
        item_id = int(entry["item_id"])
        qty = int(entry["qty"])
        if qty <= 0:
            continue
        m = menu_map.get(item_id)
        if not m:
            return {"ok": False, "error": f"Item #{item_id} tidak tersedia"}
        line_total = m["price"] * qty
        subtotal += line_total
        order_items.append((item_id, m["name"], qty, m["price"]))

    if not order_items:
        return {"ok": False, "error": "Tidak ada item valid"}

    discount = 0
    applied_code = None
    if voucher_code:
        v = validate_voucher(voucher_code, subtotal)
        if not v["ok"]:
            return {"ok": False, "error": v["error"]}
        discount = v["discount"]
        applied_code = v["code"]

    total = subtotal - discount
    user_id = user["id"]
    username = user.get("username", "")
    full_name = (user.get("first_name", "") + " " + user.get("last_name", "")).strip()

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO orders (user_id, username, full_name, status, subtotal, discount, total, voucher_code, note)
               VALUES (?,?,?,'pending',?,?,?,?,?)""",
            (user_id, username, full_name, subtotal, discount, total, applied_code, note),
        )
        order_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO order_items (order_id, item_id, item_name, qty, price) VALUES (?,?,?,?,?)",
            [(order_id, *row) for row in order_items],
        )
        conn.commit()

    if applied_code:
        consume_voucher(applied_code)

    return {"ok": True, "order_id": order_id, "total": total, "discount": discount}
