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

const AIChat = () => {
  const nav = useNavigate();

  const [step, setStep] = useState(1);
  const [category, setCategory] = useState("");
  const [issue, setIssue] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [resp, setResp] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  /* ---------------- API call ---------------- */
  const askAI = async () => {
    setBusy(true);
    setErr("");
    try {
      const prompt = `Problem: ${category}. Issue: ${issue}. ${
        errorMsg && `Error message: ${errorMsg}.`
      } Suggest fixes.`;
      const r = await fetch("http://localhost:5000/api/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const d = await r.json();
      r.ok ? setResp(d.response) : setErr(d.error || "Failed to get answer.");
    } catch (error) {
      setErr("Request failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  /* ---------------- utils ---------------- */
  const fmt = (t) =>
    t.split("\n").map((l, i) =>
      l.startsWith("- ") ? <li key={i}>{l.slice(2)}</li> : <p key={i}>{l}</p>
    );

  const next = () => setStep((s) => s + 1);
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
          Computer Repair Assistant
        </h1>

        {/* ---------- STEP 1 ---------- */}
        {step === 1 && (
          <>
            <h2 style={{ textAlign: "center", marginBottom: 24 }}>
              Select problem type
            </h2>
            <div
              style={{
                display: "flex",
                gap: 24,
                flexWrap: "wrap",
                justifyContent: "center",
              }}
            >
              {["hardware", "software", "virus/malware"].map((k) => (
                <button
                  key={k}
                  style={btnStyle(BLUE)}
                  onClick={() => {
                    setCategory(k);
                    next();
                  }}
                >
                  {k[0].toUpperCase() + k.slice(1)}
                </button>
              ))}
            </div>
          </>
        )}

        {/* ---------- STEP 2 ---------- */}
        {step === 2 && (
          <>
            <h2 style={{ textAlign: "center", marginBottom: 16 }}>
              Describe the issue
            </h2>
            <textarea
              rows={5}
              value={issue}
              placeholder={
                category === "hardware"
                  ? "Describe the hardware issue (e.g., no display, overheating, etc.)"
                  : category === "software"
                  ? "Describe the software issue (e.g., slow performance, app crashes, etc.)"
                  : "Describe the virus/malware issue (e.g., pop-ups, system slowdown, etc.)"
              }
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
        {err && (
          <p
            style={{
              marginTop: 32,
              padding: 16,
              borderRadius: 12,
              background: "#ff5c8420",
              color: RED,
            }}
          >
            {err}
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
              onClick={() => nav("/appointment-form")}
            >
              Book an Appointment
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIChat;
