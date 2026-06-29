/* ── Telegram WebApp init ─────────────────────────────────────── */
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const INIT_DATA = tg?.initData || "";

/* ── State ────────────────────────────────────────────────────── */
const cart = {};       // { item_id: { item, qty } }
let menu = {};         // { category: [item, ...] }
let useVoucher = false;

/* ── Helpers ──────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", "X-Init-Data": INIT_DATA },
    ...opts,
  });
  return res.json();
}

const riel = n => `${Number(n).toLocaleString("km-KH")}៛`;

function show(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

/* ── Menu screen ──────────────────────────────────────────────── */
function renderMenu() {
  const tabs = document.getElementById("category-tabs");
  const list = document.getElementById("menu-list");
  const cats = Object.keys(menu);
  if (!cats.length) {
    list.innerHTML = "<p class='empty-hint'>Menu kosong</p>";
    return;
  }

  tabs.innerHTML = cats.map((c, i) =>
    `<button class="cat-tab${i === 0 ? " active" : ""}" data-cat="${c}">${c}</button>`
  ).join("");

  function renderCat(activeCat) {
    list.innerHTML = "";
    tabs.querySelectorAll(".cat-tab").forEach(t =>
      t.classList.toggle("active", t.dataset.cat === activeCat)
    );
    (menu[activeCat] || []).forEach(item => {
      const qty = cart[item.id]?.qty || 0;
      const card = document.createElement("div");
      card.className = "menu-card";
      const thumb = item.image_url
        ? `<img class="menu-thumb" src="${item.image_url}" alt="" loading="lazy" onerror="this.style.display='none'">`
        : `<div class="menu-emoji">${item.emoji || "🍽️"}</div>`;
      card.innerHTML = `
        ${thumb}
        <div class="menu-info">
          <div class="menu-name">${item.name}</div>
          ${item.description ? `<div class="menu-desc">${item.description}</div>` : ""}
          <div class="menu-price">${riel(item.price)}</div>
        </div>
        <div class="qty-control">
          <button class="qty-btn minus" data-id="${item.id}">−</button>
          <span class="qty-num" id="qty-${item.id}">${qty}</span>
          <button class="qty-btn plus" data-id="${item.id}">+</button>
        </div>`;
      list.appendChild(card);
    });
  }

  renderCat(cats[0]);

  tabs.addEventListener("click", e => {
    const btn = e.target.closest(".cat-tab");
    if (btn) renderCat(btn.dataset.cat);
  });

  list.addEventListener("click", e => {
    const plus = e.target.closest(".qty-btn.plus");
    const minus = e.target.closest(".qty-btn.minus");
    if (!plus && !minus) return;
    const id = parseInt((plus || minus).dataset.id);
    const item = Object.values(menu).flat().find(i => i.id === id);
    if (!item) return;
    if (plus) {
      cart[id] = cart[id] || { item, qty: 0 };
      cart[id].qty++;
    } else {
      if (!cart[id]?.qty) return;
      cart[id].qty--;
      if (cart[id].qty === 0) delete cart[id];
    }
    document.getElementById(`qty-${id}`).textContent = cart[id]?.qty || 0;
    updateCartFab();
  });
}

function cartSubtotal() {
  return Object.values(cart).reduce((s, { item, qty }) => s + item.price * qty, 0);
}

function updateCartFab() {
  const fab = document.getElementById("btn-cart");
  const count = Object.values(cart).reduce((s, v) => s + v.qty, 0);
  if (!count) { fab.classList.add("hidden"); return; }
  fab.classList.remove("hidden");
  document.getElementById("cart-count").textContent = count;
  document.getElementById("cart-total-fab").textContent = riel(cartSubtotal());
}

/* ── Cart screen ──────────────────────────────────────────────── */
document.getElementById("cart-items").addEventListener("click", e => {
  const plus = e.target.closest(".qty-btn.plus");
  const minus = e.target.closest(".qty-btn.minus");
  if (!plus && !minus) return;
  const id = parseInt((plus || minus).dataset.id);
  if (plus) { cart[id].qty++; }
  else {
    cart[id].qty--;
    if (cart[id].qty === 0) delete cart[id];
  }
  renderCart();
  updateCartFab();
});

function renderCart() {
  const container = document.getElementById("cart-items");
  const entries = Object.values(cart);

  if (!entries.length) {
    container.innerHTML = `<div class="empty-cart">🛒 Keranjang kosong</div>`;
  } else {
    container.innerHTML = entries.map(({ item, qty }) => `
      <div class="cart-item">
        <span class="cart-emoji">${item.emoji || "☕"}</span>
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-price">${riel(item.price)} × ${qty} = <strong>${riel(item.price * qty)}</strong></div>
        </div>
        <div class="qty-control">
          <button class="qty-btn minus" data-id="${item.id}">−</button>
          <span class="qty-num">${qty}</span>
          <button class="qty-btn plus" data-id="${item.id}">+</button>
        </div>
      </div>`).join("");
  }

  updatePriceSummary();
  const empty = !entries.length;
  document.getElementById("btn-pay-cash").disabled = empty;
  document.getElementById("btn-pay-aba").disabled  = empty;
}

function updatePriceSummary() {
  const sub = cartSubtotal();
  const disc = useVoucher ? 10_000 : 0;
  const total = Math.max(0, sub - disc);

  document.getElementById("sum-subtotal").textContent = riel(sub);
  document.getElementById("sum-discount").textContent = `-${riel(disc)}`;
  document.getElementById("sum-total").textContent = riel(total);
  document.getElementById("discount-row").classList.toggle("hidden", !useVoucher);
}

/* ── Voucher toggle (sementara dinonaktifkan) ─────────────────── */
// document.getElementById("btn-toggle-voucher").addEventListener("click", () => { ... });

/* ── Address chips ────────────────────────────────────────────── */
let selectedAddr = "KD";

document.querySelectorAll(".addr-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".addr-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    selectedAddr = chip.dataset.addr;
    document.getElementById("addr-custom").value = "";
  });
});

document.getElementById("addr-custom").addEventListener("input", e => {
  if (e.target.value.trim()) {
    document.querySelectorAll(".addr-chip").forEach(c => c.classList.remove("active"));
    selectedAddr = e.target.value.trim();
  } else {
    // kembali ke chip pertama kalau input dikosongkan
    const first = document.querySelector(".addr-chip");
    first.classList.add("active");
    selectedAddr = first.dataset.addr;
  }
});

/* ── Checkout ─────────────────────────────────────────────────── */
async function doCheckout(payMethod) {
  const items = Object.values(cart).map(({ item, qty }) => ({ item_id: item.id, qty }));
  const noteBase = document.getElementById("note-input").value.trim();
  const addr = document.getElementById("addr-custom").value.trim() || selectedAddr;
  const noteWithAddr = `[${addr}] ${noteBase}`.trim();
  const note = payMethod === "ABA" ? `[Transfer ABA] ${noteWithAddr}` : noteWithAddr;

  const result = await api("/api/checkout", {
    method: "POST",
    body: JSON.stringify({ items, use_voucher: useVoucher, note }),
  });

  if (result.ok) {
    clearCart();
    showSuccess(result);
  } else if (result.error === "TOPUP_REQUIRED") {
    show("screen-cart");
    useVoucher = false;
    updatePriceSummary();
  } else if (result.error === "PARTIAL") {
    showPartialDialog(result);
  } else {
    tg?.showAlert?.(result.error || "Checkout gagal, coba lagi.");
  }
}

document.getElementById("btn-pay-cash").addEventListener("click", async () => {
  const btn = document.getElementById("btn-pay-cash");
  btn.disabled = true; btn.textContent = "Memproses...";
  await doCheckout("CASH");
  btn.disabled = false; btn.textContent = "💵 Cash";
});

document.getElementById("btn-pay-aba").addEventListener("click", () => {
  const total = cartSubtotal() - (useVoucher ? 10_000 : 0);
  document.getElementById("aba-total").textContent = riel(Math.max(0, total));
  stopPolling();
  show("screen-aba");
});

document.getElementById("btn-aba-confirm").addEventListener("click", async () => {
  const btn = document.getElementById("btn-aba-confirm");
  btn.disabled = true; btn.textContent = "Memproses...";
  await doCheckout("ABA");
  btn.disabled = false; btn.textContent = "✅ Sudah Transfer";
});

function clearCart() {
  Object.keys(cart).forEach(k => delete cart[k]);
  useVoucher = false;
  document.getElementById("note-input").value = "";
  document.getElementById("addr-custom").value = "";
  const firstChip = document.querySelector(".addr-chip");
  if (firstChip) {
    document.querySelectorAll(".addr-chip").forEach(c => c.classList.remove("active"));
    firstChip.classList.add("active");
    selectedAddr = firstChip.dataset.addr;
  }
  updateCartFab();
}

/* ── Partial dialog ───────────────────────────────────────────── */
function showPartialDialog(result) {
  const unavail = result.unavailable_items.map(i => i.item_name).join(", ");
  const body = document.getElementById("partial-body");
  body.textContent = `Item berikut habis: ${unavail}. Lanjut order tanpa item ini?`;
  document.getElementById("screen-partial").dataset.orderId = result.order_id;
  show("screen-partial");
}

document.getElementById("btn-partial-confirm").addEventListener("click", async () => {
  const oid = parseInt(document.getElementById("screen-partial").dataset.orderId);
  const result = await api("/api/checkout/confirm-partial", {
    method: "POST",
    body: JSON.stringify({ order_id: oid }),
  });
  if (result.ok) {
    showSuccess({ order_id: oid, total: 0 });
  } else {
    tg?.showAlert?.(result.error);
  }
});

document.getElementById("btn-partial-cancel").addEventListener("click", async () => {
  const oid = parseInt(document.getElementById("screen-partial").dataset.orderId);
  await api(`/api/orders/${oid}/cancel`, { method: "POST" });
  show("screen-cart");
});

/* ── Success screen ───────────────────────────────────────────── */
function showSuccess(result) {
  document.getElementById("success-order-id").textContent = "#" + result.order_id;
  document.getElementById("success-total").textContent = result.total > 0 ? riel(result.total) : "GRATIS 🎉";
  show("screen-success");
  tg?.HapticFeedback?.notificationOccurred("success");
}

/* ── Orders list ──────────────────────────────────────────────── */
function _ordersHtml(orders) {
  return orders.map(o => {
    const payBadge = o.payment_status === "PAID"
      ? `<span class="pay-badge paid">Lunas</span>`
      : `<span class="pay-badge unpaid">Belum Bayar</span>`;
    return `
      <div class="order-card" data-id="${o.id}">
        <div class="order-card-header">
          <span class="order-id">Order #${o.id}</span>
          <span class="order-status-badge ${o.status.toLowerCase()}">${o.status_label}</span>
        </div>
        <div class="order-card-meta">${o.created_at} ${payBadge}</div>
        <div class="order-card-total">${riel(o.total)}</div>
      </div>`;
  }).join("");
}

async function loadOrders() {
  const container = document.getElementById("orders-list");
  // Spinner hanya kalau container masih kosong (first load)
  if (!container.innerHTML.trim())
    container.innerHTML = `<div class="empty-orders"><div class="spinner" style="margin:0 auto"></div></div>`;

  const result = await api("/api/orders");
  if (!result.ok || !result.orders?.length) {
    container.innerHTML = `<div class="empty-orders">📋 Belum ada pesanan</div>`;
    return;
  }
  container.innerHTML = _ordersHtml(result.orders);
}

// Listener click cukup sekali, pakai event delegation
document.getElementById("orders-list").addEventListener("click", e => {
  const card = e.target.closest(".order-card");
  if (card) loadOrderDetail(parseInt(card.dataset.id));
});

async function loadOrderDetail(id) {
  document.getElementById("detail-title").textContent = "Order #" + id;
  document.getElementById("order-detail-body").innerHTML = "";
  show("screen-order-detail");
  startPolling(() => _fetchOrderDetail(id));
}

async function _fetchOrderDetail(id) {
  const body = document.getElementById("order-detail-body");
  if (!body.innerHTML.trim())
    body.innerHTML = `<div style="text-align:center;padding:32px"><div class="spinner" style="margin:0 auto"></div></div>`;

  const result = await api(`/api/orders/${id}`);
  if (!result.ok) { body.innerHTML = `<p style="padding:20px;color:var(--red)">Gagal memuat</p>`; return; }
  const o = result.order;

  const itemsHtml = o.items.map(i =>
    `<div class="detail-item-row">
      <span>${i.item_name} × ${i.qty}</span>
      <span>${riel(i.unit_price * i.qty)}</span>
    </div>`
  ).join("");

  const discHtml = o.voucher_used
    ? `<div class="detail-row"><span>Voucher</span><span class="green">-${riel(o.voucher_value)}</span></div>`
    : "";

  const payHtml = o.payment_status === "PAID"
    ? `<div class="detail-row green"><span>Pembayaran</span><span>Lunas (${o.paid_currency || ""})</span></div>`
    : `<div class="detail-row" style="color:var(--red)"><span>Pembayaran</span><span>Belum Bayar</span></div>`;

  body.innerHTML = `
    <div class="detail-status-big">${o.status_label}</div>
    <div class="detail-items">
      <strong class="section-label">ITEM</strong>
      ${itemsHtml}
    </div>
    <div class="detail-summary">
      <div class="detail-row"><span>Subtotal</span><span>${riel(o.subtotal)}</span></div>
      ${discHtml}
      <div class="detail-row detail-total"><span>Total</span><span>${riel(o.total)}</span></div>
      ${payHtml}
      ${o.note ? `<div class="detail-note">📝 ${o.note}</div>` : ""}
    </div>`;
}

/* ── Polling ──────────────────────────────────────────────────── */
let _pollTimer = null;

function startPolling(fn, ms = 3000) {
  stopPolling();
  fn(); // langsung fetch sekali
  _pollTimer = setInterval(fn, ms);
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

/* ── Navigation ───────────────────────────────────────────────── */
document.getElementById("btn-cart").addEventListener("click", () => {
  stopPolling();
  renderCart();
  show("screen-cart");
});

document.getElementById("btn-orders-icon").addEventListener("click", () => {
  document.getElementById("orders-list").innerHTML = "";
  show("screen-orders");
  startPolling(loadOrders);
});

document.getElementById("btn-back-menu").addEventListener("click", () => {
  stopPolling();
  show("screen-menu");
});
document.getElementById("btn-see-orders").addEventListener("click", () => {
  document.getElementById("orders-list").innerHTML = "";
  show("screen-orders");
  startPolling(loadOrders);
});

document.querySelectorAll(".back-btn[data-target]").forEach(btn => {
  btn.addEventListener("click", () => {
    stopPolling();
    if (btn.dataset.target === "screen-orders") {
      document.getElementById("orders-list").innerHTML = "";
      show("screen-orders");
      startPolling(loadOrders);
    } else if (btn.dataset.target === "screen-cart") {
      renderCart();
      show("screen-cart");
    } else {
      show(btn.dataset.target);
    }
  });
});

/* ── Boot ─────────────────────────────────────────────────────── */
(async () => {
  show("loading");
  try {
    const data = await api("/api/menu");
    menu = data.categories || {};
    show("screen-menu");
    renderMenu();
  } catch {
    document.querySelector(".loading-text").textContent = "Gagal memuat menu";
    document.querySelector(".spinner").style.display = "none";
  }
})();
