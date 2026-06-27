"""Owner bot commands: inline keyboard untuk manage order + push kartu ke user."""
from __future__ import annotations
import asyncio

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, OWNER_ID, WEBAPP_URL
from state_machine import (
    STATUS_LABEL,
    get_order,
    get_pending_orders,
    get_user_orders,
    transition,
)


def _order_text(o: dict) -> str:
    items_text = "\n".join(
        f"  • {i['item_name']} x{i['qty']}  Rp {i['price']*i['qty']:,}"
        for i in o.get("items", [])
    )
    discount_line = f"  Diskon : -Rp {o['discount']:,}\n" if o["discount"] else ""
    return (
        f"🧾 *Order #{o['id']}*\n"
        f"👤 {o['full_name'] or o['username'] or o['user_id']}\n"
        f"📋 Status : {STATUS_LABEL.get(o['status'], o['status'])}\n"
        f"📝 Note   : {o['note'] or '-'}\n\n"
        f"{items_text}\n\n"
        f"  Subtotal: Rp {o['subtotal']:,}\n"
        f"{discount_line}"
        f"  *Total  : Rp {o['total']:,}*\n"
        f"  Waktu   : {o['created_at']}"
    )


def _order_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    from state_machine import TRANSITIONS
    buttons = [
        InlineKeyboardButton(STATUS_LABEL[s], callback_data=f"status:{order_id}:{s}")
        for s in TRANSITIONS.get(status, [])
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh:{order_id}")])
    return InlineKeyboardMarkup(rows)


async def _is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _is_owner(update):
        return
    await update.message.reply_text(
        "☕ *Jakarta Cafe — Owner Panel*\n\n"
        "/pending — lihat order masuk\n"
        "/order \\<id\\> — detail 1 order\n"
        "/push \\<user\\_id\\> — kirim kartu promo ke user",
        parse_mode="MarkdownV2",
    )


async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _is_owner(update):
        return
    orders = get_pending_orders()
    if not orders:
        await update.message.reply_text("Tidak ada order pending saat ini.")
        return
    for o in orders:
        full = get_order(o["id"])
        await update.message.reply_text(
            _order_text(full),
            parse_mode="Markdown",
            reply_markup=_order_keyboard(full["id"], full["status"]),
        )


async def cmd_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await _is_owner(update):
        return
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /order <id>")
        return
    o = get_order(int(args[0]))
    if not o:
        await update.message.reply_text("Order tidak ditemukan.")
        return
    await update.message.reply_text(
        _order_text(o),
        parse_mode="Markdown",
        reply_markup=_order_keyboard(o["id"], o["status"]),
    )


async def cmd_push(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Push promo card to a specific user."""
    if not await _is_owner(update):
        return
    args = ctx.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /push <user_id> [pesan opsional]")
        return
    target_uid = int(args[0])
    msg = " ".join(args[1:]) if len(args) > 1 else "☕ Ada promo spesial buat kamu hari ini!"
    bot: Bot = ctx.bot
    try:
        await bot.send_message(
            chat_id=target_uid,
            text=f"🎁 *Dari Jakarta Cafe*\n\n{msg}\n\nOrder sekarang 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Buka Menu", url=WEBAPP_URL)
            ]]),
        )
        await update.message.reply_text(f"✅ Kartu terkirim ke user {target_uid}")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal kirim: {e}")


async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != OWNER_ID:
        return

    data = query.data
    if data.startswith("status:"):
        _, oid, new_status = data.split(":")
        result = transition(int(oid), new_status)
        if result["ok"]:
            o = get_order(int(oid))
            await query.edit_message_text(
                _order_text(o),
                parse_mode="Markdown",
                reply_markup=_order_keyboard(o["id"], o["status"]),
            )
            # Notify customer
            try:
                await ctx.bot.send_message(
                    chat_id=o["user_id"],
                    text=f"🔔 *Order #{o['id']}* diperbarui\nStatus: {result['label']}",
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        else:
            await query.answer(result["error"], show_alert=True)

    elif data.startswith("refresh:"):
        oid = int(data.split(":")[1])
        o = get_order(oid)
        if o:
            await query.edit_message_text(
                _order_text(o),
                parse_mode="Markdown",
                reply_markup=_order_keyboard(o["id"], o["status"]),
            )


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("order", cmd_order))
    app.add_handler(CommandHandler("push", cmd_push))
    app.add_handler(CallbackQueryHandler(callback_handler))
    return app
