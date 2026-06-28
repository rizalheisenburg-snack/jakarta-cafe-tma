"""initData verification + checkout logic."""
from __future__ import annotations
import hashlib
import hmac
import json
import time
import urllib.parse

from config import BOT_TOKEN
from db import get_conn
from state_machine import VOUCHER_VALUE, apply_voucher, auto_pay_if_free

MAX_AGE = 86_400  # 24 jam anti-replay


def verify_init_data(init_data: str) -> dict | None:
    """Return parsed user dict kalau initData valid, else None."""
    params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        return None

    # Anti-replay: tolak kalau lebih tua dari 24 jam
    auth_date = int(params.get("auth_date", 0))
    if time.time() - auth_date > MAX_AGE:
        return None

    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        return None

    return json.loads(params.get("user", "{}"))


def checkout(
    user: dict,
    items: list[dict],
    use_voucher: bool,
    note: str,
) -> dict:
    """
    items: [{"item_id": int, "qty": int}, ...]
    use_voucher: True kalau customer mau pakai voucher fisik

    Return:
      {"ok": True, "order_id": int, "total": int, "voucher_result": dict|None}
      {"ok": False, "error": str}
      {"ok": False, "error": "TOPUP_REQUIRED", "topup_needed": int}
      {"ok": False, "error": "PARTIAL", "available_items": list, "order_id": int}
    """
    if not items:
        return {"ok": False, "error": "Keranjang kosong"}

    # ── Baca menu LIVE dari DB (harga & stok dari server, bukan client) ────────
    with get_conn() as conn:
        menu_rows = conn.execute("SELECT * FROM menu_items").fetchall()
    menu_map = {r["id"]: dict(r) for r in menu_rows}

    valid_items = []
    unavailable_items = []
    subtotal = 0

    for entry in items:
        item_id = int(entry["item_id"])
        qty = int(entry["qty"])
        if qty <= 0:
            continue
        m = menu_map.get(item_id)
        if not m:
            unavailable_items.append({"item_id": item_id, "reason": "tidak ada"})
            continue
        if not m["available"]:
            unavailable_items.append({"item_id": item_id, "item_name": m["name"], "reason": "habis"})
            continue
        subtotal += m["price"] * qty
        valid_items.append((item_id, m["name"], qty, m["price"]))

    if not valid_items:
        return {"ok": False, "error": "Semua item tidak tersedia"}

    # ── Voucher ────────────────────────────────────────────────────────────────
    voucher_result = None
    voucher_value = 0

    if use_voucher:
        voucher_result = apply_voucher(subtotal)
        if voucher_result["result"] == "TOPUP_REQUIRED":
            return {
                "ok": False,
                "error": "TOPUP_REQUIRED",
                "topup_needed": voucher_result["topup_needed"],
                "message": voucher_result["message"],
            }
        voucher_value = voucher_result["voucher_value"]

    # ── Ada item habis sebagian → PARTIAL_PENDING ──────────────────────────────
    initial_status = "PARTIAL_PENDING" if unavailable_items else "PENDING"

    user_id = user["id"]
    username = user.get("username", "")
    full_name = (user.get("first_name", "") + " " + user.get("last_name", "")).strip()

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO orders
               (user_id, username, full_name, status, subtotal, voucher_used, voucher_value, note)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, username, full_name, initial_status,
             subtotal, 1 if use_voucher else 0, voucher_value, note),
        )
        order_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO order_items (order_id, item_id, item_name, qty, unit_price) VALUES (?,?,?,?,?)",
            [(order_id, *row) for row in valid_items],
        )
        conn.commit()

    # Auto-pay kalau total = 0 (voucher pas)
    auto_paid = auto_pay_if_free(order_id)

    if unavailable_items:
        return {
            "ok": False,
            "error": "PARTIAL",
            "order_id": order_id,
            "available_items": valid_items,
            "unavailable_items": unavailable_items,
            "subtotal": subtotal,
            "voucher_result": voucher_result,
        }

    return {
        "ok": True,
        "order_id": order_id,
        "subtotal": subtotal,
        "voucher_value": voucher_value,
        "total": subtotal - voucher_value,
        "auto_paid": auto_paid,
        "voucher_result": voucher_result,
    }


def confirm_partial(order_id: int, user_id: int) -> dict:
    """Customer setuju lanjut walau ada item yang dibuang."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status, user_id FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "error": "Order tidak ditemukan"}
        if row["user_id"] != user_id:
            return {"ok": False, "error": "Forbidden"}
        if row["status"] != "PARTIAL_PENDING":
            return {"ok": False, "error": "Order bukan dalam status PARTIAL_PENDING"}

        conn.execute(
            "UPDATE orders SET status='PENDING', updated_at=datetime('now') WHERE id=?",
            (order_id,),
        )
        conn.commit()
    return {"ok": True, "order_id": order_id, "status": "PENDING"}
