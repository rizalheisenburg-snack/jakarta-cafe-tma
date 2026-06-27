/* ── Telegram WebApp init ─────────────────────────────────────── */
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const INIT_DATA = tg?.initData || "";

/* ── State ────────────────────────────────────────────────────── */
const cart = {};          // { item_id: { item, qty } }
let menu = {};            // { category: [item, ...] }
let voucher = null;       // { code, discount, description } | null
let currentScreen = null;

/* ── API ──────────────────────────────────────────────────────── */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", "X-Init-Data": INIT_DATA },
    ...opts,
  });
  return res.json();
}

/* ── Screen router ────────────────────────────────────────────── */
function show(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  currentScreen = id;
}

/* ── Format Rupiah ────────────────────────────────────────────── */
const rp = n => "Rp " + Number(n).toLocaleString("id-ID");

/* ── Menu screen ──────────────────────────────────────────────── */
function renderMenu() {
  const tabs = document.getElementById("category-tabs");
  const list = document.getElementById("menu-list");
  const cats = Object.keys(menu);
  if (!cats.length) { list.innerHTML = "<p style='color:var(--hint);padding:32px;text-align:center'>Menu kosong</p>"; return; }

  tabs.innerHTML = cats.map((c, i) =>
    `<button class="cat-tab${i === 0 ? " active" : ""}" data-cat="${c}">${c}</button>`
  ).join("");

  function renderCat(activeCat) {
    list.innerHTML = "";
    tabs.querySelectorAll(".cat-tab").forEach(t => t.classList.toggle("active", t.dataset.cat === activeCat));
    (menu[activeCat] || []).forEach(item => {
      const qty = cart[item.id]?.qty || 0;
      const card = document.createElement("div");
      card.className = "menu-card";
      card.dataset.id = item.id;
      card.innerHTML = `
        <div class="menu-emoji">${item.emoji || "☕"}</div>
        <div class="menu-info">
          <div class="menu-name">${item.name}</div>
          ${item.description ? `<div class="menu-desc">${item.description}</div>` : ""}
          <div class="menu-price">${rp(item.price)}</div>
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
    const allItems = Object.values(menu).flat();
    const item = allItems.find(i => i.id === id);
    if (!item) return;

    if (plus) {
      cart[id] = cart[id] || { item, qty: 0 };
      cart[id].qty++;
    } else {
      if (!cart[id] || cart[id].qty === 0) return;
      cart[id].qty--;
      if (cart[id].qty === 0) delete cart[id];
    }
    document.getElementById(`qty-${id}`).textContent = cart[id]?.qty || 0;
    updateCartFab();
  });
}

function updateCartFab() {
  const fab = document.getElementById("btn-cart");
  const total = cartTotal();
  const count = Object.values(cart).reduce((s, v) => s + v.qty, 0);
  if (count === 0) { fab.classList.add("hidden"); return; }
  fab.classList.remove("hidden");
  document.getElementById("cart-count").textContent = count;
  document.getElementById("cart-total-fab").textContent = rp(total);
}

function cartSubtotal() {
  return Object.values(cart).reduce((s, { item, qty }) => s + item.price * qty, 0);
}
function cartTotal() {
  return Math.max(0, cartSubtotal() - (voucher?.discount || 0));
}

/* ── Cart screen ──────────────────────────────────────────────── */
function renderCart() {
  const container = document.getElementById("cart-items");
  const entries = Object.values(cart);

  if (!entries.length) {
    container.innerHTML = `<div class="empty-cart">🛒 Keranjang kosong<br><small>Tambah item dari menu dulu</small></div>`;
  } else {
    container.innerHTML = entries.map(({ item, qty }) => `
      <div class="cart-item">
        <span style="font-size:28px">${item.emoji || "☕"}</span>
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-price">${rp(item.price)} × ${qty} = <strong>${rp(item.price * qty)}</strong></div>
        </div>
        <div class="qty-control">
          <button class="qty-btn minus" data-id="${item.id}">−</button>
          <span class="qty-num">${qty}</span>
          <button class="qty-btn plus" data-id="${item.id}">+</button>
        </div>
      </div>`).join("");

    container.addEventListener("click", e => {
      const plus = e.target.closest(".qty-btn.plus");
      const minus = e.target.closest(".qty-btn.minus");
      if (!plus && !minus) return;
      const id = parseInt((plus || minus).dataset.id);
      if (plus) { cart[id].qty++; }
      else {
        cart[id].qty--;
        if (cart[id].qty === 0) delete cart[id];
      }
      voucher = null; // reset voucher on cart change
      renderCart();
      updateCartFab();
    }, { once: true });
  }

  updatePriceSummary();

  document.getElementById("btn-checkout").disabled = !entries.length;
}

function updatePriceSummary() {
  const sub = cartSubtotal();
  const disc = voucher?.discount || 0;
  const total = cartTotal();

  document.getElementById("sum-subtotal").textContent = rp(sub);
  document.getElementById("sum-discount").textContent = "-" + rp(disc);
  document.getElementById("sum-total").textContent = rp(total);

  const discRow = document.getElementById("discount-row");
  discRow.classList.toggle("hidden", disc === 0);
}

/* ── Voucher ──────────────────────────────────────────────────── */
document.getElementById("btn-apply-voucher").addEventListener("click", async () => {
  const code = document.getElementById("voucher-input").value.trim();
  const msgEl = document.getElementById("voucher-msg");
  if (!code) return;

  const sub = cartSubtotal();
  const result = await api("/api/voucher/check", {
    method: "POST",
    body: JSON.stringify({ code, subtotal: sub }),
  });

  msgEl.className = "voucher-msg";
  if (result.ok) {
    voucher = result;
    msgEl.classList.add("ok");
    msgEl.textContent = `✅ Voucher berlaku! Hemat ${result.description}`;
  } else {
    voucher = null;
    msgEl.classList.add("err");
    msgEl.textContent = "❌ " + result.error;
  }
  updatePriceSummary();
});

/* ── Checkout ─────────────────────────────────────────────────── */
document.getElementById("btn-checkout").addEventListener("click", async () => {
  const btn = document.getElementById("btn-checkout");
  btn.disabled = true;
  btn.textContent = "Memproses...";

  const items = Object.values(cart).map(({ item, qty }) => ({ item_id: item.id, qty }));
  const note = document.getElementById("note-input").value.trim();

  const result = await api("/api/checkout", {
    method: "POST",
    body: JSON.stringify({ items, voucher_code: voucher?.code || null, note }),
  });

  btn.disabled = false;
  btn.textContent = "Pesan Sekarang";

  if (result.ok) {
    // Clear cart
    Object.keys(cart).forEach(k => delete cart[k]);
    voucher = null;
    document.getElementById("voucher-input").value = "";
    document.getElementById("note-input").value = "";
    updateCartFab();

    document.getElementById("success-order-id").textContent = "#" + result.order_id;
    document.getElementById("success-total").textContent = rp(result.total);
    show("screen-success");
    tg?.HapticFeedback?.notificationOccurred("success");
  } else {
    tg?.showAlert?.(result.error || "Checkout gagal, coba lagi.");
  }
});

/* ── Orders list ──────────────────────────────────────────────── */
async function loadOrders() {
  const container = document.getElementById("orders-list");
  container.innerHTML = `<div class="empty-orders"><div class="spinner" style="margin:0 auto"></div></div>`;
  const result = await api("/api/orders");
  if (!result.ok || !result.orders?.length) {
    container.innerHTML = `<div class="empty-orders">📋 Belum ada pesanan</div>`;
    return;
  }
  container.innerHTML = result.orders.map(o => `
    <div class="order-card" data-id="${o.id}">
      <div class="order-card-header">
        <span class="order-id">Order #${o.id}</span>
        <span class="order-status-badge ${o.status}">${o.status_label}</span>
      </div>
      <div class="order-card-meta">${o.created_at}</div>
      <div class="order-card-total">${rp(o.total)}</div>
    </div>`).join("");

  container.addEventListener("click", e => {
    const card = e.target.closest(".order-card");
    if (!card) return;
    loadOrderDetail(parseInt(card.dataset.id));
  });
}

async function loadOrderDetail(id) {
  document.getElementById("detail-title").textContent = "Order #" + id;
  show("screen-order-detail");
  const body = document.getElementById("order-detail-body");
  body.innerHTML = `<div style="text-align:center;padding:32px"><div class="spinner" style="margin:0 auto"></div></div>`;

  const result = await api(`/api/orders/${id}`);
  if (!result.ok) { body.innerHTML = `<p style="padding:20px;color:var(--red)">Gagal memuat order</p>`; return; }
  const o = result.order;

  const itemsHtml = o.items.map(i => `
    <div class="detail-item-row">
      <span>${i.item_name} × ${i.qty}</span>
      <span>${rp(i.price * i.qty)}</span>
    </div>`).join("");

  const discountHtml = o.discount ? `<div class="detail-row"><span>Diskon</span><span class="green">-${rp(o.discount)}</span></div>` : "";

  body.innerHTML = `
    <div class="detail-status-big">${o.status_label}</div>
    <div class="detail-items">
      <strong style="font-size:13px;color:var(--hint)">ITEM</strong>
      ${itemsHtml}
    </div>
    <div class="detail-summary">
      <div class="detail-row"><span>Subtotal</span><span>${rp(o.subtotal)}</span></div>
      ${discountHtml}
      <div class="detail-row detail-total"><span>Total</span><span>${rp(o.total)}</span></div>
      ${o.note ? `<div class="detail-note">📝 ${o.note}</div>` : ""}
      ${o.voucher_code ? `<div class="detail-note">🎟 Voucher: ${o.voucher_code}</div>` : ""}
    </div>`;
}

/* ── Navigation wiring ────────────────────────────────────────── */
document.getElementById("btn-cart").addEventListener("click", () => {
  renderCart();
  show("screen-cart");
});

document.getElementById("btn-orders-icon").addEventListener("click", () => {
  loadOrders();
  show("screen-orders");
});

document.getElementById("btn-back-menu").addEventListener("click", () => show("screen-menu"));
document.getElementById("btn-see-orders").addEventListener("click", () => {
  loadOrders();
  show("screen-orders");
});

document.querySelectorAll(".back-btn[data-target]").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.target;
    if (target === "screen-orders") { loadOrders(); }
    show(target);
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
  } catch (e) {
    document.querySelector(".loading-text").textContent = "Gagal memuat menu 😢";
    document.querySelector(".spinner").style.display = "none";
  }
})();
