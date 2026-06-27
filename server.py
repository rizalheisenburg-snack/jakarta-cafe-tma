"""HTTP server — aiohttp. Melayani API + static webapp."""
from __future__ import annotations
import json
import pathlib

from aiohttp import web

from checkout_flow import checkout, verify_init_data
from config import OWNER_ID
from db import get_conn
from state_machine import (
    get_order,
    get_user_orders,  # noqa: F401 — dipakai di api_orders
    transition,
    validate_voucher,
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
    init_data = request.headers.get("X-Init-Data", "")
    return verify_init_data(init_data)


# ── Menu ────────────────────────────────────────────────────────────────────


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


# ── Voucher check ────────────────────────────────────────────────────────────


@routes.post("/api/voucher/check")
async def api_voucher_check(request):
    body = await request.json()
    code = body.get("code", "")
    subtotal = int(body.get("subtotal", 0))
    result = validate_voucher(code, subtotal)
    return _json(result)


# ── Checkout ─────────────────────────────────────────────────────────────────


@routes.post("/api/checkout")
async def api_checkout(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)

    body = await request.json()
    items = body.get("items", [])
    voucher = body.get("voucher_code") or None
    note = body.get("note", "")

    result = checkout(user, items, voucher, note)
    return _json(result, 200 if result["ok"] else 400)


# ── Orders ───────────────────────────────────────────────────────────────────


@routes.get("/api/orders")
async def api_orders(request):
    user = _auth(request)
    if not user:
        return _json({"ok": False, "error": "Unauthorized"}, 401)
    orders = get_user_orders(user["id"])
    return _json({"ok": True, "orders": orders})


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


# ── Owner: update status ──────────────────────────────────────────────────────


@routes.post("/api/owner/orders/{order_id}/status")
async def api_owner_status(request):
    user = _auth(request)
    if not user or user["id"] != OWNER_ID:
        return _json({"ok": False, "error": "Forbidden"}, 403)
    oid = int(request.match_info["order_id"])
    body = await request.json()
    new_status = body.get("status", "")
    result = transition(oid, new_status)
    return _json(result, 200 if result["ok"] else 400)


# ── Static webapp ─────────────────────────────────────────────────────────────


@routes.get("/{tail:.*}")
async def static_files(request):
    tail = request.match_info["tail"] or "index.html"
    path = WEBAPP_DIR / tail
    if not path.exists() or not path.is_file():
        path = WEBAPP_DIR / "index.html"
    return web.FileResponse(path)


def build_app() -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    return app
