import { useEffect, useState } from "react";
import SiteHeader from "../components/SiteHeader.jsx";
import { CheckIcon, ResetIcon } from "../components/icons.jsx";
import { getPublicProducts, submitCandidate } from "../api/client.js";

const CNIC_PATTERN = /^\d{5}-?\d{7}-?\d{1}$/;

export default function EntryForm() {
  const [pageState, setPageState] = useState("loading"); // loading | ready
  const [products, setProducts] = useState([]);
  const [loadError, setLoadError] = useState("");

  const [productId, setProductId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [cnic, setCnic] = useState("");
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("idle");
  const [serverError, setServerError] = useState("");
  const [confirmation, setConfirmation] = useState(null);

  useEffect(() => {
    getPublicProducts()
      .then((productList) => {
        setProducts(productList);
        if (productList.length > 0) setProductId(String(productList[0].id));
        setPageState("ready");
      })
      .catch((err) => {
        setLoadError(err.message);
        setPageState("ready");
      });
  }, []);

  function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = {};

    if (!productId) {
      nextErrors.product = "Choose a product.";
    }
    if (!name.trim()) {
      nextErrors.name = "Name is required.";
    }

    const trimmedEmail = email.trim();
    const trimmedCnic = cnic.trim();
    if (!trimmedEmail && !trimmedCnic) {
      nextErrors.contact = "Enter an email address, a CNIC, or both.";
    } else if (trimmedCnic && !CNIC_PATTERN.test(trimmedCnic)) {
      nextErrors.contact = "CNIC must be 13 digits, e.g. 12345-1234567-1.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setStatus("submitting");
    setServerError("");

    submitCandidate({
      product_id: Number(productId),
      name: name.trim(),
      email: trimmedEmail || null,
      cnic: trimmedCnic || null,
    })
      .then((result) => {
        setConfirmation(result);
        setStatus("success");
      })
      .catch((err) => {
        setStatus("idle");
        if (err.status === 409) {
          setServerError("You're already entered for this product.");
        } else {
          setServerError(err.message);
        }
      });
  }

  function handleEnterAnother() {
    setStatus("idle");
    setConfirmation(null);
    setName("");
    setEmail("");
    setCnic("");
    setErrors({});
    setServerError("");
  }

  if (pageState === "loading") {
    return (
      <div className="site-shell">
        <SiteHeader />
        <main className="site-main">
          <p className="loading-text">
            <span className="spinner" aria-hidden="true" />
            Loading…
          </p>
        </main>
      </div>
    );
  }

  if (status === "success" && confirmation) {
    return (
      <div className="site-shell">
        <SiteHeader />
        <main className="site-main">
          <div className="panel panel--raised">
            <h1>You're in.</h1>
            <p>
              Thanks, <strong>{confirmation.name}</strong> , you're entered for{" "}
              <strong>{confirmation.product_name}</strong>.
            </p>
            <button type="button" onClick={handleEnterAnother}>
              <ResetIcon />
              Submit another entry
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="site-main">
        <div className="panel panel--raised">
          <h1 className="heading-serif">Enter the ballot</h1>
          {loadError && <p className="error-text">{loadError}</p>}
          {products.length === 0 ? (
            <p className="empty-state">No products are open for entries yet.</p>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              <div className="field">
                <label htmlFor="product">Product</label>
                <select
                  id="product"
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                >
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name}
                    </option>
                  ))}
                </select>
                {errors.product && <p className="error-text">{errors.product}</p>}
              </div>

              <div className="field">
                <label htmlFor="name">Name</label>
                <input id="name" value={name} onChange={(e) => setName(e.target.value)} />
                {errors.name && <p className="error-text">{errors.name}</p>}
              </div>

              <div className="field">
                <label htmlFor="email">Email (optional if CNIC is given)</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="cnic">CNIC (optional if email is given)</label>
                <input
                  id="cnic"
                  value={cnic}
                  onChange={(e) => setCnic(e.target.value)}
                  placeholder="12345-1234567-1"
                />
              </div>

              {errors.contact && <p className="error-text">{errors.contact}</p>}
              {serverError && <p className="error-text">{serverError}</p>}

              <button type="submit" className="primary-button" disabled={status === "submitting"}>
                <CheckIcon />
                {status === "submitting" ? "Submitting…" : "Submit entry"}
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
