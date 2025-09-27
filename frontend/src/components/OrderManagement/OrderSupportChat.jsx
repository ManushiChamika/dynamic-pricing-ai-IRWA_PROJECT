import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

/* ---------------- palette / helpers ---------------- */
const BLUE = "#0a84ff";
const RED = "#ff3b6b";
const DARK = "#1e293b";
const neon = (c) => `0 0 6px ${c}, 0 0 14px ${c}77`;

/* button factory */
const btnStyle = (bg, disabled) => ({
  border: "none",
  padding: "12px 26px",
  fontWeight: 600,
  borderRadius: 10,
  cursor: disabled ? "not-allowed" : "pointer",
  background: bg,
  color: "#fff",
  boxShadow: neon(bg),
  opacity: disabled ? 0.65 : 1,
  transition: "transform 0.15s",
});

const OrderSupportChat = () => {
  const nav = useNavigate();

  const [step, setStep] = useState(1);
  const [email, setEmail] = useState(""); 
  const [orderId, setOrderId] = useState("");
  const [issue, setIssue] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [error, setError] = useState("");
  const [resp, setResp] = useState("");
  const [busy, setBusy] = useState(false);

  // Function to fetch the latest successful order by customer email
  const fetchLatestOrder = async (userEmail) => {
    try {
      const response = await fetch(`http://localhost:5000/api/orders/all`);
      const data = await response.json();
      console.log("orders:", data);

      const userOrders = data.filter(order => order.email === userEmail);
      console.log("orders:", userOrders);
      if (userOrders.length > 0) {
        const latestOrder = userOrders.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];

        if (latestOrder._id) {
          setOrderId(latestOrder._id);
        } else {
          setError("No successful orders found.");
        }
      } else {
        setError("No successful orders found.");
      }
    } catch (err) {
      console.error(err);
      setError("Error fetching order. Please try again.");
    }
  };

  /* ---------------- API call ---------------- */
  const askAI = async () => {
    setBusy(true);
    setError("");
    try {
      const prompt = `Order ID: ${orderId}. Issue: ${issue}. ${
        errorMsg && `Error message: ${errorMsg}.`
      } Suggest fixes or order details.`;
      const r = await fetch("http://localhost:5000/api/order-support/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const d = await r.json();
      r.ok ? setResp(d.response) : setError(d.error || "Failed to get answer.");
    } catch (err) {
      console.error(err);
      setError("Request failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  /* ---------------- utils ---------------- */
  const fmt = (t) =>
    t.split("\n").map((l, i) =>
      l.startsWith("- ") ? <li key={i}>{l.slice(2)}</li> : <p key={i}>{l}</p>
    );

  const next = async () => {
    if (step === 1 && email.trim()) {
      await fetchLatestOrder(email.trim());
    }
    setStep((s) => s + 1);
  };

  const back = () => setStep((s) => s - 1);

  /* ---------------- UI ---------------- */
  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 25% 15%,#002d60 0%,#00152e 55%,#000a1c 100%)",
        fontFamily: "Inter, sans-serif",
        display: "flex",
        alignItems: "center",
        padding: 40,
        color: "#e2e8f0",
      }}
    >
      <div
        style={{
          width: "75vw",
          maxWidth: 960,
          margin: "0 auto",
          background: "rgba(255,255,255,0.08)",
          backdropFilter: "blur(12px)",
          borderRadius: 22,
          boxShadow: "0 10px 28px rgba(0,0,0,0.32)",
          padding: "50px 60px",
        }}
      >
        <h1
          style={{
            textAlign: "center",
            marginBottom: 36,
            fontSize: 32,
            color: BLUE,
            textShadow: neon(BLUE),
          }}
        >
          Order Support Assistant
        </h1>

        {/* ---------- STEP 1 ---------- */}
        {step === 1 && (
          <>
            <h2 style={{ textAlign: "center", marginBottom: 24 }}>
              Enter your Email
            </h2>
            <input
              type="email"
              value={email}
              placeholder="Enter your Email"
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: "100%",
                padding: 16,
                borderRadius: 12,
                border: "1px solid #334155",
                background: "rgba(0,0,0,0.25)",
                color: "#e2e8f0",
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 32,
              }}
            >
              <button style={btnStyle(DARK)} onClick={back}>
                Back
              </button>
              <button
                style={btnStyle(BLUE, !email.trim())}
                onClick={next}
                disabled={!email.trim()}
              >
                Next
              </button>
            </div>
          </>
        )}

        {/* ---------- STEP 2 ---------- */}
        {step === 2 && (
          <>
            <h2 style={{ textAlign: "center", marginBottom: 16 }}>
              Describe the issue with your order
            </h2>
            <textarea
              rows={5}
              value={issue}
              placeholder="Describe the issue (e.g., missing items, delivery delay, wrong product, etc.)"
              onChange={(e) => setIssue(e.target.value)}
              style={{
                width: "100%",
                padding: 16,
                borderRadius: 12,
                border: "1px solid #334155",
                background: "rgba(0,0,0,0.25)",
                color: "#e2e8f0",
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 32,
              }}
            >
              <button style={btnStyle(DARK)} onClick={back}>
                Back
              </button>
              <button
                style={btnStyle(BLUE, !issue.trim())}
                onClick={next}
                disabled={!issue.trim()}
              >
                Next
              </button>
            </div>
          </>
        )}

        {/* ---------- STEP 3 ---------- */}
        {step === 3 && (
          <>
            <h2 style={{ textAlign: "center", marginBottom: 16 }}>
              Error message (optional)
            </h2>
            <textarea
              rows={5}
              value={errorMsg}
              placeholder="Enter the error message (if any)"
              onChange={(e) => setErrorMsg(e.target.value)}
              style={{
                width: "100%",
                padding: 16,
                borderRadius: 12,
                border: "1px solid #334155",
                background: "rgba(0,0,0,0.25)",
                color: "#e2e8f0",
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 32,
              }}
            >
              <button style={btnStyle(DARK)} onClick={back}>
                Back
              </button>
              <button
                style={btnStyle(RED, busy)}
                onClick={askAI}
                disabled={busy}
              >
                {busy ? "Generating…" : "Submit"}
              </button>
            </div>
          </>
        )}

        {/* ---------- ERROR ---------- */}
        {error && (
          <p
            style={{
              marginTop: 32,
              padding: 16,
              borderRadius: 12,
              background: "#ff5c8420",
              color: RED,
            }}
          >
            {error}
          </p>
        )}

        {/* ---------- RESPONSE ---------- */}
        {resp && (
          <div style={{ marginTop: 48 }}>
            <h2
              style={{
                textAlign: "center",
                color: RED,
                textShadow: neon(RED),
                marginBottom: 20,
              }}
            >
              AI Suggestions
            </h2>
            <div
              style={{
                background: "rgba(0,0,0,0.35)",
                padding: 28,
                borderRadius: 16,
                lineHeight: 1.7,
              }}
            >
              {fmt(resp)}
            </div>
            <button
              style={{ ...btnStyle(BLUE), width: "100%", marginTop: 36 }}
              onClick={() => nav("/OrderList")}
            >
              Update Order
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderSupportChat;
