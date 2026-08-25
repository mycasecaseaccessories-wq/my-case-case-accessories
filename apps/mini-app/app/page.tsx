"use client";

import { useEffect, useMemo, useState } from "react";

type Product = {
  id: string;
  name: string;
  description?: string | null;
  price: string | number;
  sku: string;
  category_id?: string | null;
};
type Category = { id: string; name: string };
type CartLine = { product: Product; quantity: number };

const API = (process.env.NEXT_PUBLIC_CENTRAL_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

function money(value: string | number) {
  return `${Number(value).toLocaleString("en-US", { minimumFractionDigits: 2 })} MMK`;
}

export default function MiniAppPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [selected, setSelected] = useState<Product | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [orderMessage, setOrderMessage] = useState("");
  const [sessionState, setSessionState] = useState<"checking" | "verified" | "unavailable" | "invalid">("checking");
  const [initData, setInitData] = useState("");
  const [orders, setOrders] = useState<Array<{ id: string; status: string; total: string | number }>>([]);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<{ id: string; status: string; total: string | number } | null>(
    null,
  );

  function telegramHeaders(): Record<string, string> {
    return initData ? { "X-Telegram-Init-Data": initData } : {};
  }

  useEffect(() => {
    const saved = window.localStorage.getItem("my-case-mini-cart");
    if (saved) setCart(JSON.parse(saved));
    const webApp = (
      window as Window & { Telegram?: { WebApp?: { ready?: () => void; expand?: () => void; initData?: string } } }
    ).Telegram?.WebApp;
    webApp?.ready?.();
    webApp?.expand?.();
    if (webApp?.initData) {
      setInitData(webApp.initData);
      fetch(`${API}/auth/telegram/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: webApp.initData }),
      })
        .then(async (response) => {
          setSessionState(response.ok ? "verified" : "invalid");
          if (response.ok) {
            const cartResponse = await fetch(`${API}/telegram/cart`, {
              headers: { "X-Telegram-Init-Data": webApp.initData || "" },
            });
            if (cartResponse.ok) {
              const centralCart = await cartResponse.json();
              const catalogResponse = await fetch(`${API}/catalog/products`);
              const catalog = catalogResponse.ok ? ((await catalogResponse.json()) as Product[]) : [];
              setCart(
                (centralCart.items || []).flatMap((item: { product_id: string; quantity: number }) => {
                  const product = catalog.find((candidate) => candidate.id === item.product_id);
                  return product ? [{ product, quantity: item.quantity }] : [];
                }),
              );
            }
          }
        })
        .catch(() => setSessionState("invalid"));
    } else {
      setSessionState("unavailable");
    }
    Promise.all([
      fetch(`${API}/catalog/products`).then((response) => {
        if (!response.ok) throw new Error("catalog");
        return response.json();
      }),
      fetch(`${API}/catalog/categories`).then((response) => {
        if (!response.ok) throw new Error("categories");
        return response.json();
      }),
    ])
      .then(([productData, categoryData]) => {
        setProducts(productData);
        setCategories(categoryData);
      })
      .catch(() => setError("Catalog ကို ခဏတာ မဖွင့်နိုင်သေးပါ။ ထပ်ကြိုးစားပေးပါ။"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (sessionState !== "verified") window.localStorage.setItem("my-case-mini-cart", JSON.stringify(cart));
  }, [cart, sessionState]);

  async function loadOrders() {
    if (sessionState !== "verified") return;
    const response = await fetch(`${API}/telegram/orders`, { headers: telegramHeaders() });
    if (!response.ok) throw new Error("orders");
    setOrders(await response.json());
    setOrdersOpen(true);
  }

  const visible = useMemo(
    () =>
      products.filter(
        (product) =>
          (!category || product.category_id === category) &&
          (!query || `${product.name} ${product.sku}`.toLowerCase().includes(query.toLowerCase())),
      ),
    [products, query, category],
  );
  const total = cart.reduce((sum, line) => sum + Number(line.product.price) * line.quantity, 0);

  function add(product: Product) {
    setCart((current) => {
      const existing = current.find((line) => line.product.id === product.id);
      if (existing)
        return current.map((line) =>
          line.product.id === product.id ? { ...line, quantity: Math.min(line.quantity + 1, 999) } : line,
        );
      return [...current, { product, quantity: 1 }];
    });
    setCartOpen(true);
  }
  function change(productId: string, delta: number) {
    setCart((current) =>
      current.flatMap((line) =>
        line.product.id === productId
          ? line.quantity + delta > 0 && line.quantity + delta <= 999
            ? [{ ...line, quantity: line.quantity + delta }]
            : line.quantity + delta <= 0
              ? []
              : [line]
          : [line],
      ),
    );
  }
  async function checkout() {
    if (!name.trim() || !phone.trim() || !cart.length) return;
    setOrderMessage("Order တင်နေပါတယ်...");
    try {
      if (sessionState === "verified") {
        const linkResponse = await fetch(`${API}/telegram/link`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...telegramHeaders() },
          body: JSON.stringify({ full_name: name.trim(), phone: phone.trim() }),
        });
        if (!linkResponse.ok) throw new Error("link");
        for (const line of cart) {
          const itemResponse = await fetch(`${API}/telegram/cart/items`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...telegramHeaders() },
            body: JSON.stringify({ product_id: line.product.id, quantity: line.quantity }),
          });
          if (!itemResponse.ok) throw new Error("cart");
        }
        const response = await fetch(`${API}/telegram/cart/checkout`, {
          method: "POST",
          headers: { ...telegramHeaders(), "X-Checkout-Idempotency-Key": `mini-app:${crypto.randomUUID()}` },
        });
        if (!response.ok) throw new Error("order");
        const order = await response.json();
        setCart([]);
        setOrderMessage(`Order အောင်မြင်ပါပြီ။ ${order.id} · ${money(order.total)}`);
        return;
      }
      const lookup = await fetch(`${API}/customers/lookup?phone=${encodeURIComponent(phone.trim())}`);
      const matches = lookup.ok ? await lookup.json() : [];
      const customer =
        matches[0] ||
        (await fetch(`${API}/customers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full_name: name.trim(), phone: phone.trim() }),
        }).then((response) => {
          if (!response.ok) throw new Error("customer");
          return response.json();
        }));
      const response = await fetch(`${API}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customer.id,
          customer_name: name.trim(),
          customer_phone: phone.trim(),
          items: cart.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
        }),
      });
      if (!response.ok) throw new Error("order");
      const order = await response.json();
      setCart([]);
      setOrderMessage(`Order အောင်မြင်ပါပြီ။ ${order.id} · ${money(order.total)}`);
    } catch {
      setOrderMessage(
        "Order မအောင်မြင်ပါ။ Stock၊ Telegram link နှင့် customer အချက်အလက်ကို ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ။",
      );
    }
  }

  return (
    <main className="store">
      <div className="shell">
        <header className="topbar">
          <div className="brand">My Case / Telegram Store</div>
          <div className="top-actions">
            {sessionState === "verified" && (
              <button className="secondary" onClick={() => void loadOrders()}>
                My Orders
              </button>
            )}
            <button className="cart-button" onClick={() => setCartOpen((open) => !open)} aria-label="Open cart">
              Cart ({cart.reduce((sum, line) => sum + line.quantity, 0)})
            </button>
          </div>
        </header>
        <section className="hero">
          <p className="eyebrow">Inside Telegram</p>
          <h1>Cases that fit your everyday.</h1>
          <p>
            My Case accessories ကို Central Store နဲ့တူညီတဲ့ catalog, ဈေးနှုန်းနဲ့ checkout flow ဖြင့် ရွေးချယ်ဝယ်ယူပါ။
          </p>
        </section>
        <section className="controls">
          <input
            className="search"
            aria-label="Search products"
            placeholder="Search by product name or SKU"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <div className="category-row">
            <button className={`category ${!category ? "active" : ""}`} onClick={() => setCategory("")}>
              All
            </button>
            {categories.map((item) => (
              <button
                className={`category ${category === item.id ? "active" : ""}`}
                key={item.id}
                onClick={() => setCategory(item.id)}
              >
                {item.name}
              </button>
            ))}
          </div>
        </section>
        {error && (
          <p className="notice" role="alert">
            {error}
          </p>
        )}
        {sessionState === "invalid" && (
          <p className="notice" role="alert">
            Telegram session ကို အတည်ပြုမရသေးပါ။ Customer account/order history များကို မပြသပါ။
          </p>
        )}
        {ordersOpen && (
          <section className="cart-panel" aria-label="Order history">
            <div className="panel-heading">
              <h2>My Orders</h2>
              <button className="secondary" onClick={() => setOrdersOpen(false)}>
                Close
              </button>
            </div>
            {!orders.length ? (
              <div className="empty">Order history မရှိသေးပါ။</div>
            ) : (
              orders.map((order) => (
                <button
                  className="cart-line"
                  key={order.id}
                  onClick={async () => {
                    const response = await fetch(`${API}/telegram/orders/${order.id}`, { headers: telegramHeaders() });
                    if (response.ok) setSelectedOrder(await response.json());
                  }}
                >
                  <div>
                    <strong>{order.id}</strong>
                    <br />
                    <span className="sku">Status: {order.status}</span>
                  </div>
                  <span>{money(order.total)}</span>
                </button>
              ))
            )}
          </section>
        )}
        {selectedOrder && (
          <section className="cart-panel" role="dialog" aria-label="Order detail">
            <button className="secondary" onClick={() => setSelectedOrder(null)}>
              Close
            </button>
            <h2>Order Detail</h2>
            <p>{selectedOrder.id}</p>
            <p>
              Status: <strong>{selectedOrder.status}</strong>
            </p>
            <p>
              Total: <strong>{money(selectedOrder.total)}</strong>
            </p>
          </section>
        )}
        {cartOpen && (
          <section className="cart-panel" aria-label="Cart">
            <h2>Your cart</h2>
            {!cart.length ? (
              <div className="empty">Cart လွတ်နေပါတယ်။</div>
            ) : (
              <>
                {cart.map((line) => (
                  <div className="cart-line" key={line.product.id}>
                    <div>
                      <strong>{line.product.name}</strong>
                      <br />
                      <span className="sku">{money(Number(line.product.price) * line.quantity)}</span>
                    </div>
                    <div className="qty">
                      <button
                        onClick={() => change(line.product.id, -1)}
                        aria-label={`Remove one ${line.product.name}`}
                      >
                        −
                      </button>
                      <span>{line.quantity}</span>
                      <button onClick={() => change(line.product.id, 1)} aria-label={`Add one ${line.product.name}`}>
                        +
                      </button>
                    </div>
                  </div>
                ))}
                <strong>Total: {money(total)}</strong>
                <div className="form">
                  <input placeholder="Customer name" value={name} onChange={(event) => setName(event.target.value)} />
                  <input placeholder="Phone" value={phone} onChange={(event) => setPhone(event.target.value)} />
                  <button className="primary" onClick={checkout} disabled={!name.trim() || !phone.trim()}>
                    Checkout
                  </button>
                  {orderMessage && <p role="status">{orderMessage}</p>}
                </div>
              </>
            )}
          </section>
        )}
        {loading ? (
          <div className="empty">Catalog loading...</div>
        ) : !visible.length ? (
          <div className="empty">ဒီရှာဖွေမှုနဲ့ product မတွေ့ပါ။</div>
        ) : (
          <section className="grid" aria-label="Product catalog">
            {visible.map((product) => (
              <article className="card" key={product.id}>
                <div className="card-art" aria-hidden="true">
                  MC
                </div>
                <h2>{product.name}</h2>
                <p>{product.description || "Quality everyday accessory"}</p>
                <span className="price">{money(product.price)}</span>
                <span className="sku">SKU: {product.sku}</span>
                <button className="secondary" onClick={() => setSelected(product)}>
                  View details
                </button>
                <button className="primary" onClick={() => add(product)}>
                  Add to cart
                </button>
              </article>
            ))}
          </section>
        )}
        {selected && (
          <div className="cart-panel" role="dialog" aria-label="Product detail">
            <button className="secondary" onClick={() => setSelected(null)}>
              Close
            </button>
            <h2>{selected.name}</h2>
            <p>{selected.description || "Quality everyday accessory"}</p>
            <strong>{money(selected.price)}</strong>
            <span className="sku">SKU: {selected.sku}</span>
            <button
              className="primary"
              onClick={() => {
                add(selected);
                setSelected(null);
              }}
            >
              Add to cart
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
