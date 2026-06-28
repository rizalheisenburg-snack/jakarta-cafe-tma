"""State machine dapur + payment logic."""
from __future__ import annotations
from db import get_conn

# ── State dapur ───────────────────────────────────────────────────────────────
# PRE_CHECK     : row baru lahir, server lagi validasi stok
# PARTIAL_PENDING: ada item habis, nunggu customer terima/batal
# PENDING       : order masuk, nunggu owner
# CONFIRMED     : owner terima — window cancel customer TUTUP
# PREPARING     : owner mulai masak
# DONE          : selesai [terminal]
# REJECTED      : owner tolak [terminal]
# CANCELLED     : dibatalkan [terminal]

TRANSITIONS: dict[str, list[str]] = {
    "PRE_CHECK":       ["PARTIAL_PENDING", "PENDING", "CANCELLED"],
    "PARTIAL_PENDING": ["PENDING", "CANCELLED"],
    "PENDING":         ["CONFIRMED", "REJECTED", "CANCELLED"],
    "CONFIRMED":       ["PREPARING", "CANCELLED"],
    "PREPARING":       ["DONE"],
    "DONE":            [],
    "REJECTED":        [],
    "CANCELLED":       [],
}

TERMINAL = {"DONE", "REJECTED", "CANCELLED"}

STATUS_LABEL: dict[str, str] = {
    "PRE_CHECK":       "🔄 Memproses",
    "PARTIAL_PENDING": "⚠️ Item Sebagian Habis",
    "PENDING":         "⏳ Menunggu Konfirmasi",
    "CONFIRMED":       "✅ Dikonfirmasi",
    "PREPARING":       "👨‍🍳 Sedang Dibuat",
    "DONE":            "🎉 Selesai",
    "REJECTED":        "❌ Ditolak Owner",
    "CANCELLED":       "🚫 Dibatalkan",
}

VOUCHER_VALUE = 10_000  # riel, fixed — ga ada kembalian, ga bisa nyimpen receh

# ── Voucher logic ─────────────────────────────────────────────────────────────
# 3 skenario:
#   belanja > 10k  → potong 10k, sisanya bayar cash/transfer
#   belanja = 10k  → total 0, GRATIS, auto-PAID
#   belanja < 10k  → TOPUP_REQUIRED: customer harus genepin ke 10k atau batal


def apply_voucher(subtotal: int) -> dict:
    """
    Return dict dengan field:
      - ok: True selalu (voucher selalu diterima, beda hasilnya)
      - result: 'APPLIED' | 'FREE' | 'TOPUP_REQUIRED'
      - voucher_value: berapa riel yang dipotong (0 kalau TOPUP_REQUIRED)
      - topup_needed: berapa riel yang harus ditambahin (0 kalau bukan TOPUP)
      - total: subtotal setelah potongan
      - message: pesan untuk customer
    """
    if subtotal > VOUCHER_VALUE:
        return {
            "ok": True,
            "result": "APPLIED",
            "voucher_value": VOUCHER_VALUE,
            "topup_needed": 0,
            "total": subtotal - VOUCHER_VALUE,
            "message": f"Voucher dipotong {VOUCHER_VALUE:,} riel",
        }
    elif subtotal == VOUCHER_VALUE:
        return {
            "ok": True,
            "result": "FREE",
            "voucher_value": VOUCHER_VALUE,
            "topup_needed": 0,
            "total": 0,
            "message": "GRATIS! Voucher menutup seluruh tagihan",
        }
    else:  # subtotal < VOUCHER_VALUE
        topup = VOUCHER_VALUE - subtotal
        return {
            "ok": True,
            "result": "TOPUP_REQUIRED",
            "voucher_value": 0,
            "topup_needed": topup,
            "total": subtotal,
            "message": (
                f"Belanja kurang dari {VOUCHER_VALUE:,} riel. "
                f"Tambah {topup:,} riel lagi atau batalkan order."
            ),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def can_customer_cancel(status: str) -> bool:
    """Customer hanya boleh cancel selagi PENDING."""
    return status == "PENDING"


def can_owner_cancel(status: str) -> bool:
    return status not in TERMINAL


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
    result = []
    for r in rows:
        o = dict(r)
        o["status_label"] = STATUS_LABEL.get(o["status"], o["status"])
        result.append(o)
    return result


def get_pending_orders() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status='PENDING' ORDER BY created_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


# ── Transisi ──────────────────────────────────────────────────────────────────

def transition(order_id: int, new_status: str, actor: str = "owner") -> dict:
    """
    actor: 'owner' | 'customer' | 'system'
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status, payment_status FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "error": "Order tidak ditemukan"}

        current = row["status"]

        # Validasi cancel customer
        if new_status == "CANCELLED" and actor == "customer":
            if not can_customer_cancel(current):
                return {
                    "ok": False,
                    "error": "Order sudah dikonfirmasi, tidak bisa dibatalkan",
                }

        if new_status not in TRANSITIONS.get(current, []):
            return {
                "ok": False,
                "error": f"Tidak bisa dari '{current}' ke '{new_status}'",
            }

        conn.execute(
            "UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?",
            (new_status, order_id),
        )
        conn.commit()

    return {"ok": True, "status": new_status, "label": STATUS_LABEL[new_status]}


# ── Payment ───────────────────────────────────────────────────────────────────

def mark_paid(order_id: int, paid_currency: str = "RIEL") -> dict:
    """
    paid_currency: 'RIEL' | 'USD'
    Omzet hanya ngitung order yang PAID.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status, payment_status, total FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "error": "Order tidak ditemukan"}
        if row["payment_status"] == "PAID":
            return {"ok": False, "error": "Order sudah lunas"}
        if row["status"] in ("REJECTED", "CANCELLED"):
            return {"ok": False, "error": "Order tidak valid untuk dilunasi"}

        conn.execute(
            """UPDATE orders
               SET payment_status='PAID', paid_currency=?, paid_at=datetime('now'),
                   updated_at=datetime('now')
               WHERE id=?""",
            (paid_currency.upper(), order_id),
        )
        conn.commit()

    return {"ok": True, "total": row["total"]}


def auto_pay_if_free(order_id: int) -> bool:
    """Kalau total=0 (voucher pas), langsung PAID otomatis. Return True kalau di-auto."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT total, payment_status FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not row or row["payment_status"] == "PAID":
            return False
        if row["total"] == 0:
            conn.execute(
                """UPDATE orders
                   SET payment_status='PAID', paid_currency='RIEL',
                       paid_at=datetime('now'), updated_at=datetime('now')
                   WHERE id=?""",
                (order_id,),
            )
            conn.commit()
            return True
    return False


# ── Omzet ─────────────────────────────────────────────────────────────────────

def get_omzet(bulan: int, tahun: int) -> dict:
    """
    Omzet = SUM(total) WHERE payment_status='PAID'.
    paid_at disimpan UTC → date(paid_at) = hari kerja yang bener.
    Shift: UTC hour < 12 = siang, >= 12 = malam.
    """
    periode = f"{tahun}-{bulan:02d}"
    with get_conn() as conn:
        summary = conn.execute("""
            SELECT
                COUNT(*)                                          AS total_order,
                COALESCE(SUM(total), 0)                          AS omzet_riel,
                SUM(CASE WHEN payment_status='PAID' THEN 1 ELSE 0 END) AS lunas,
                SUM(CASE WHEN status='CANCELLED'    THEN 1 ELSE 0 END) AS batal,
                SUM(CASE WHEN status='REJECTED'     THEN 1 ELSE 0 END) AS ditolak,
                SUM(CASE WHEN paid_currency='USD'   THEN 1 ELSE 0 END) AS bayar_usd
            FROM orders
            WHERE strftime('%Y-%m', paid_at) = ?
              AND payment_status = 'PAID'
        """, (periode,)).fetchone()

        top_items = conn.execute("""
            SELECT oi.item_name, SUM(oi.qty) AS total_qty
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE strftime('%Y-%m', o.paid_at) = ?
              AND o.payment_status = 'PAID'
            GROUP BY oi.item_name
            ORDER BY total_qty DESC
            LIMIT 5
        """, (periode,)).fetchall()

    return {
        "periode": periode,
        "total_order": summary["total_order"],
        "omzet_riel": summary["omzet_riel"],
        "lunas": summary["lunas"],
        "batal": summary["batal"],
        "ditolak": summary["ditolak"],
        "bayar_usd": summary["bayar_usd"],
        "top_items": [dict(r) for r in top_items],
    }
