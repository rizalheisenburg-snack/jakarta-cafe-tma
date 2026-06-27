"""Order state machine + voucher validation."""
from __future__ import annotations
from db import get_conn

TRANSITIONS: dict[str, list[str]] = {
    "pending":    ["confirmed", "cancelled"],
    "confirmed":  ["preparing", "cancelled"],
    "preparing":  ["ready",     "cancelled"],
    "ready":      ["done",      "cancelled"],
    "done":       [],
    "cancelled":  [],
}

STATUS_LABEL = {
    "pending":   "⏳ Menunggu Konfirmasi",
    "confirmed": "✅ Dikonfirmasi",
    "preparing": "👨‍🍳 Sedang Dibuat",
    "ready":     "🔔 Siap Diambil",
    "done":      "🎉 Selesai",
    "cancelled": "❌ Dibatalkan",
}


def transition(order_id: int, new_status: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            return {"ok": False, "error": "Order tidak ditemukan"}

        current = row["status"]
        if new_status not in TRANSITIONS.get(current, []):
            return {"ok": False, "error": f"Tidak bisa dari '{current}' ke '{new_status}'"}

        conn.execute(
            "UPDATE orders SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
            (new_status, order_id),
        )
        conn.commit()
    return {"ok": True, "status": new_status, "label": STATUS_LABEL[new_status]}


def validate_voucher(code: str, subtotal: int) -> dict:
    with get_conn() as conn:
        v = conn.execute(
            "SELECT * FROM vouchers WHERE code=? AND active=1", (code.upper(),)
        ).fetchone()

    if not v:
        return {"ok": False, "error": "Kode voucher tidak valid"}
    if v["max_uses"] is not None and v["used_count"] >= v["max_uses"]:
        return {"ok": False, "error": "Voucher sudah habis"}
    if subtotal < v["min_order"]:
        return {
            "ok": False,
            "error": f"Minimum order Rp {v['min_order']:,} untuk voucher ini",
        }

    if v["discount_type"] == "percent":
        discount = int(subtotal * v["discount_value"] / 100)
    else:
        discount = min(v["discount_value"], subtotal)

    return {
        "ok": True,
        "code": v["code"],
        "discount": discount,
        "description": (
            f"{v['discount_value']}% off"
            if v["discount_type"] == "percent"
            else f"Rp {v['discount_value']:,} off"
        ),
    }


def consume_voucher(code: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE vouchers SET used_count=used_count+1 WHERE code=?", (code.upper(),)
        )
        conn.commit()


def get_order(order_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            return None
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ).fetchall()

    order = dict(row)
    order["items"] = [dict(i) for i in items]
    order["status_label"] = STATUS_LABEL.get(order["status"], order["status"])
    return order


def get_user_orders(user_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ).fetchall()
    orders = []
    for r in rows:
        o = dict(r)
        o["status_label"] = STATUS_LABEL.get(o["status"], o["status"])
        orders.append(o)
    return orders


def get_pending_orders() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status='pending' ORDER BY created_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]
