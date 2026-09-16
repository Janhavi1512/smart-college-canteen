// ============================== CART (index.html) ==============================
const cart = {}; // { id: {name, price, qty, max} }

function updateCartUI() {
    const cartItems = document.getElementById("cartItems");
    const cartCount = document.getElementById("cartCount");
    const cartTotal = document.getElementById("cartTotal");
    const placeOrderBtn = document.getElementById("placeOrderBtn");
    if (!cartItems) return;

    const ids = Object.keys(cart).filter((id) => cart[id].qty > 0);

    if (ids.length === 0) {
        cartItems.innerHTML = '<p class="empty-cart">Your cart is empty. Tap "+" on any item to add it.</p>';
        cartCount.textContent = "0";
        cartTotal.textContent = "₹0.00";
        placeOrderBtn.disabled = true;
        return;
    }

    let total = 0;
    let count = 0;
    cartItems.innerHTML = ids
        .map((id) => {
            const item = cart[id];
            const sub = item.price * item.qty;
            total += sub;
            count += item.qty;
            return `<div class="cart-line"><span>${item.name} x${item.qty}</span><span>₹${sub.toFixed(2)}</span></div>`;
        })
        .join("");

    cartCount.textContent = count;
    cartTotal.textContent = `₹${total.toFixed(2)}`;
    placeOrderBtn.disabled = false;
}

function initMenuPage() {
    const grid = document.getElementById("menuGrid");
    if (!grid) return;

    grid.addEventListener("click", (e) => {
        const btn = e.target.closest(".qty-btn");
        if (!btn || btn.disabled) return;
        const id = btn.dataset.id;

        if (btn.classList.contains("plus")) {
            const name = btn.dataset.name;
            const price = parseFloat(btn.dataset.price);
            const max = parseInt(btn.dataset.max, 10);
            if (!cart[id]) cart[id] = { name, price, qty: 0, max };
            if (cart[id].qty < max) cart[id].qty += 1;
        } else if (btn.classList.contains("minus")) {
            if (cart[id] && cart[id].qty > 0) cart[id].qty -= 1;
        }

        const qtyEl = document.getElementById(`qty-${id}`);
        if (qtyEl) qtyEl.textContent = cart[id] ? cart[id].qty : 0;
        updateCartUI();
    });

    // Category filter
    const filterBar = document.getElementById("filterBar");
    filterBar.addEventListener("click", (e) => {
        const btn = e.target.closest(".filter-btn");
        if (!btn) return;
        document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const cat = btn.dataset.cat;
        document.querySelectorAll(".menu-card").forEach((card) => {
            card.style.display = cat === "all" || card.dataset.cat === cat ? "" : "none";
        });
    });

    document.getElementById("placeOrderBtn").addEventListener("click", async () => {
        const errorEl = document.getElementById("orderError");
        errorEl.textContent = "";
        const customerName = document.getElementById("customerName").value.trim() || "Guest";

        const cartPayload = Object.keys(cart)
            .filter((id) => cart[id].qty > 0)
            .map((id) => ({ id: parseInt(id, 10), qty: cart[id].qty }));

        if (cartPayload.length === 0) return;

        try {
            const res = await fetch("/order", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_name: customerName, cart: cartPayload }),
            });
            const data = await res.json();
            if (!res.ok) {
                errorEl.textContent = data.error || "Something went wrong. Please try again.";
                return;
            }
            window.location.href = data.redirect;
        } catch (err) {
            errorEl.textContent = "Network error. Please try again.";
        }
    });

    updateCartUI();
}

// ============================== COUNTER (counter.html) ==============================
function initCounterPage() {
    const lookupBtn = document.getElementById("lookupBtn");
    if (!lookupBtn) return;

    const manualCode = document.getElementById("manualCode");
    const lookupError = document.getElementById("lookupError");
    const orderDetails = document.getElementById("orderDetails");

    async function lookupOrder(code) {
        lookupError.textContent = "";
        try {
            const res = await fetch("/api/counter/lookup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ order_code: code }),
            });
            const data = await res.json();
            if (!res.ok) {
                lookupError.textContent = data.error || "Order not found";
                orderDetails.style.display = "none";
                return;
            }
            renderOrder(data);
        } catch (e) {
            lookupError.textContent = "Network error looking up order.";
        }
    }

    function renderOrder(order) {
        document.getElementById("odCode").textContent = order.order_code;
        document.getElementById("odCustomer").textContent = order.customer_name;
        document.getElementById("odTime").textContent = order.created_at;
        document.getElementById("odTotal").textContent = `₹${order.total_amount.toFixed(2)}`;

        const itemsBody = document.getElementById("odItems");
        itemsBody.innerHTML = order.items
            .map((it) => `<tr><td>${it.name}</td><td>${it.qty}</td><td>₹${it.subtotal.toFixed(2)}</td></tr>`)
            .join("");

        const payStatusEl = document.getElementById("odPayStatus");
        payStatusEl.textContent = order.payment_status;
        payStatusEl.className = "badge " + (order.payment_status === "paid" ? "available" : "unavailable");

        const payControls = document.getElementById("payControls");
        const payMsg = document.getElementById("payMsg");
        payMsg.textContent = "";
        payControls.style.display = order.payment_status === "paid" ? "none" : "flex";

        orderDetails.style.display = "block";
        orderDetails.dataset.orderCode = order.order_code;
    }

    lookupBtn.addEventListener("click", () => {
        const code = manualCode.value.trim().toUpperCase();
        if (code) lookupOrder(code);
    });
    manualCode.addEventListener("keydown", (e) => {
        if (e.key === "Enter") lookupBtn.click();
    });

    document.getElementById("markPaidBtn").addEventListener("click", async () => {
        const code = orderDetails.dataset.orderCode;
        const mode = document.getElementById("paymentMode").value;
        const payMsg = document.getElementById("payMsg");
        try {
            const res = await fetch("/api/counter/pay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ order_code: code, payment_mode: mode }),
            });
            const data = await res.json();
            if (!res.ok) {
                payMsg.className = "error-msg";
                payMsg.textContent = data.error || "Could not confirm payment.";
                return;
            }
            payMsg.className = "success-msg";
            payMsg.textContent = "Payment confirmed! Order marked as served.";
            lookupOrder(code); // refresh view
        } catch (e) {
            payMsg.className = "error-msg";
            payMsg.textContent = "Network error confirming payment.";
        }
    });

    // Camera QR scanning via html5-qrcode (loaded from CDN in counter.html)
    const startBtn = document.getElementById("startScanBtn");
    const stopBtn = document.getElementById("stopScanBtn");
    let html5QrCode = null;

    startBtn.addEventListener("click", async () => {
        if (typeof Html5Qrcode === "undefined") {
            lookupError.textContent = "Camera scanner library failed to load. Use manual entry instead.";
            return;
        }
        try {
            html5QrCode = new Html5Qrcode("qr-reader");
            await html5QrCode.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: 220 },
                (decodedText) => {
                    manualCode.value = decodedText;
                    lookupOrder(decodedText.trim().toUpperCase());
                    stopScanning();
                },
                () => {} // ignore per-frame scan failures
            );
            startBtn.style.display = "none";
            stopBtn.style.display = "inline-block";
        } catch (e) {
            lookupError.textContent = "Could not access camera. Use manual entry instead.";
        }
    });

    function stopScanning() {
        if (html5QrCode) {
            html5QrCode.stop().catch(() => {});
        }
        startBtn.style.display = "inline-block";
        stopBtn.style.display = "none";
    }
    stopBtn.addEventListener("click", stopScanning);
}

// ============================== REVIEWS (reviews.html) ==============================
function initReviewsPage() {
    const form = document.getElementById("reviewForm");
    if (!form) return;

    let selectedRating = 0;
    const stars = document.querySelectorAll("#starSelect .star");
    stars.forEach((star) => {
        star.addEventListener("click", () => {
            selectedRating = parseInt(star.dataset.val, 10);
            stars.forEach((s) => {
                s.classList.toggle("selected", parseInt(s.dataset.val, 10) <= selectedRating);
                s.textContent = parseInt(s.dataset.val, 10) <= selectedRating ? "★" : "☆";
            });
        });
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("reviewMsg");
        msg.className = "error-msg";
        const menuId = document.getElementById("reviewItem").value;
        const customerName = document.getElementById("reviewName").value.trim() || "Anonymous";
        const comment = document.getElementById("reviewComment").value.trim();

        if (!menuId) { msg.textContent = "Please select a menu item."; return; }
        if (selectedRating === 0) { msg.textContent = "Please select a star rating."; return; }

        try {
            const res = await fetch("/api/reviews", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ menu_id: menuId, customer_name: customerName, rating: selectedRating, comment }),
            });
            const data = await res.json();
            if (!res.ok) { msg.textContent = data.error || "Could not submit review."; return; }
            msg.className = "success-msg";
            msg.textContent = "Thanks for your review!";
            setTimeout(() => window.location.reload(), 900);
        } catch (err) {
            msg.textContent = "Network error submitting review.";
        }
    });
}

// ============================== ADMIN (admin.html) ==============================
function initAdminPage() {
    const table = document.querySelector(".admin-table");
    if (!document.querySelector(".toggle-avail-btn")) return;

    document.querySelectorAll(".toggle-avail-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const id = btn.dataset.id;
            const res = await fetch("/api/admin/toggle_availability", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id }),
            });
            const data = await res.json();
            if (res.ok) {
                const badge = document.getElementById(`avail-badge-${id}`);
                badge.textContent = data.available ? "Available" : "Unavailable";
                badge.className = "badge " + (data.available ? "available" : "unavailable");
            }
        });
    });

    document.querySelectorAll(".stock-input").forEach((input) => {
        input.addEventListener("change", async () => {
            const id = input.dataset.id;
            const stock_qty = parseInt(input.value, 10) || 0;
            const res = await fetch("/api/admin/update_stock", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id, stock_qty }),
            });
            if (res.ok) {
                const badge = document.getElementById(`avail-badge-${id}`);
                if (badge) {
                    badge.textContent = stock_qty > 0 ? "Available" : "Unavailable";
                    badge.className = "badge " + (stock_qty > 0 ? "available" : "unavailable");
                }
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initMenuPage();
    initCounterPage();
    initReviewsPage();
    initAdminPage();
});
