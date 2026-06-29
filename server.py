"""HTTP server — aiohttp. Melayani API + static webapp."""
from __future__ import annotations
import json
import logging
import pathlib

log = logging.getLogger(__name__)

from aiohttp import web

from checkout_flow import checkout, confirm_partial, verify_init_data
from config import OWNER_ID
from db import get_conn
from state_machine import (
    get_order,
    get_user_orders,
    mark_paid,
    transition,
)

WEBAPP_DIR = pathlib.Path(__file__).parent / "webapp"
routes = web.RouteTableDef()


def _json(data, status=200):
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        content_type="application/json",
        status=status,
    )


def _auth(request: web.Request) -> dict | None:
    return verify_init_data(request.headers.get("X-Init-Data", ""))


# ── Menu ──────────────────────────────────────────────────────────────────────

@routes.get("/api/menu")
async def api_menu(request):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM menu_items WHERE available=1 ORDER BY category, name"
        ).fetchall()
    by_cat: dict[str, list] = {}
    for r in rows:
        d = dict(r)
        by_cat.setdefault(d["category"], []).append(d)
    return _json({"categories": by_cat})


# ── Checkout ──────────────────────────────────────────────────────────────────

@routes.post("/api/checkout")
async def api_checkout(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    try:
        body = await request.json()
        result = checkout(
            user=user,
            items=body.get("items", []),
            use_voucher=bool(body.get("use_voucher", False)),
            note=body.get("note", ""),
        )
        # Kirim notif ke owner kalau order masuk (ok atau PARTIAL)
        if result.get("ok") or result.get("error") == "PARTIAL":
            await _notify_owner_new_order(request, result.get("order_id"))
        return _json(result, 200 if result["ok"] else 400)
    except Exception as e:
        log.exception("checkout error")
        return _json({"ok": False, "error": f"Server error: {e}"}, 500)


async def _notify_owner_new_order(request: web.Request, order_id: int | None):
    if not order_id:
        return
    bot = request.app["bot"]
    if not bot:
        return
    try:
        from owner_console import _order_keyboard, _order_text
        from state_machine import get_order
        o = get_order(order_id)
        if not o:
            return
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await bot.send_message(
            chat_id=OWNER_ID,
            text=f"🔔 *Order baru masuk!*\n\n{_order_text(o)}",
            parse_mode="Markdown",
            reply_markup=_order_keyboard(o["id"], o["status"], o["payment_status"]),
        )
    except Exception:
        log.exception("gagal kirim notif owner")


@routes.post("/api/checkout/confirm-partial")
async def api_confirm_partial(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    body = await request.json()
    result = confirm_partial(int(body.get("order_id", 0)), user["id"])
    return _json(result, 200 if result["ok"] else 400)


# ── Orders ────────────────────────────────────────────────────────────────────

@routes.get("/api/orders")
async def api_orders(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    return _json({"ok": True, "orders": get_user_orders(user["id"])})


@routes.get("/api/orders/{order_id}")
async def api_order_detail(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    oid = int(request.match_info["order_id"])
    o = get_order(oid)
    if not o:
        return _json({"ok": False, "error": "Tidak ditemukan"}, 404)
    if o["user_id"] != user["id"] and user["id"] != OWNER_ID:
        return _json({"ok": False, "error": "Forbidden"}, 403)
    return _json({"ok": True, "order": o})


@routes.post("/api/orders/{order_id}/cancel")
async def api_cancel_order(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    oid = int(request.match_info["order_id"])
    result = transition(oid, "CANCELLED", actor="customer")
    return _json(result, 200 if result["ok"] else 400)


# ── Owner ─────────────────────────────────────────────────────────────────────

@routes.post("/api/owner/orders/{order_id}/status")
async def api_owner_status(request):
    user = _auth(request)
    if not user or user["id"] != OWNER_ID:
        return _json({"ok": False, "error": "Forbidden"}, 403)
    oid = int(request.match_info["order_id"])
    body = await request.json()
    result = transition(oid, body.get("status", ""), actor="owner")
    return _json(result, 200 if result["ok"] else 400)


@routes.post("/api/owner/orders/{order_id}/pay")
async def api_owner_pay(request):
    user = _auth(request)
    if not user or user["id"] != OWNER_ID:
        return _json({"ok": False, "error": "Forbidden"}, 403)
    oid = int(request.match_info["order_id"])
    body = await request.json()
    result = mark_paid(oid, body.get("currency", "RIEL"))
    return _json(result, 200 if result["ok"] else 400)


# ── Static ────────────────────────────────────────────────────────────────────

@routes.get("/{tail:.*}")
async def static_files(request):
    tail = request.match_info["tail"] or "index.html"
    path = WEBAPP_DIR / tail
    if not path.exists() or not path.is_file():
        path = WEBAPP_DIR / "index.html"
    return web.FileResponse(path)


def build_app(bot=None) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.add_routes(routes)
    return app
