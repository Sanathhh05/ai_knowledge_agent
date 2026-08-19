"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";

const API = "http://127.0.0.1:8000";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "signup") {
        const res = await fetch(`${API}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          let errorMessage = `Signup failed (${res.status})`;
          if (Array.isArray(body.detail)) {
            errorMessage = body.detail.map((err: any) => err.msg).join(", ");
          } else if (body.detail) {
            errorMessage = body.detail;
          }
          throw new Error(errorMessage);
        }
        // After signup, auto-login
      }

      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        let errorMessage = `Login failed (${res.status})`;
        if (Array.isArray(body.detail)) {
          errorMessage = body.detail.map((err: any) => err.msg).join(", ");
        } else if (body.detail) {
          errorMessage = body.detail;
        }
        throw new Error(errorMessage);
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/sources");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-primary)",
        padding: "1rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          background: "var(--bg-card)",
          border: "1px solid var(--border-primary)",
          borderRadius: 24,
          padding: "3rem 2.5rem",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
        }}
      >
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          {/* Logo Mark */}
          <div style={{ display: "flex", justifyContent: "center", marginBottom: "1rem" }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "50%",
                background: "var(--accent-glow)",
                color: "var(--accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: "-0.02em",
              color: "var(--text-primary)",
              marginBottom: 8,
            }}
          >
            RAMBO
          </div>
          <div style={{ color: "var(--text-secondary)", fontSize: 15 }}>
            Your AI Knowledge Assistant
          </div>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid var(--danger)",
              color: "var(--danger)",
              borderRadius: 8,
              padding: "0.75rem 1rem",
              marginBottom: "1rem",
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <label
            style={{
              display: "block",
              marginBottom: 6,
              fontSize: 13,
              color: "var(--text-secondary)",
            }}
          >
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "0.65rem 0.85rem",
              background: "var(--bg-input)",
              border: "1px solid var(--border-primary)",
              borderRadius: 8,
              color: "var(--text-primary)",
              fontSize: 14,
              marginBottom: "1rem",
              outline: "none",
            }}
            placeholder="you@example.com"
          />

          <label
            style={{
              display: "block",
              marginBottom: 6,
              fontSize: 13,
              color: "var(--text-secondary)",
            }}
          >
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "0.65rem 0.85rem",
              background: "var(--bg-input)",
              border: "1px solid var(--border-primary)",
              borderRadius: 8,
              color: "var(--text-primary)",
              fontSize: 14,
              marginBottom: "1.5rem",
              outline: "none",
            }}
            placeholder="Min 8 chars, 1 uppercase, 1 digit"
          />

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.75rem",
              background: loading ? "var(--text-muted)" : "var(--accent)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 15,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>
        </form>

        {/* Toggle */}
        <div
          style={{
            textAlign: "center",
            marginTop: "1.25rem",
            fontSize: 13,
            color: "var(--text-secondary)",
          }}
        >
          {mode === "login" ? (
            <>
              No account?{" "}
              <button
                onClick={() => {
                  setMode("signup");
                  setError("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: 13,
                }}
              >
                Sign Up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: 13,
                }}
              >
                Sign In
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
