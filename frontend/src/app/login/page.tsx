"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${base}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      });
      if (!res.ok) {
        setError("Not authorized. Check username/password.");
        setLoading(false);
        return;
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('auth:updated'));
      }
      router.push("/reference");
    } catch (err) {
      setError("Login failed. Try again.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-8 max-w-md mx-auto space-y-6">
      <h1 className="text-2xl font-semibold">Login</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <div className="space-y-1">
          <label className="text-sm">Username</label>
          <input
            className="w-full border rounded px-3 py-2 bg-transparent"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm">Password</label>
          <input
            className="w-full border rounded px-3 py-2 bg-transparent"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="mt-2 bg-black text-white rounded px-4 py-2 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
        {error && <div className="text-sm text-red-600">{error}</div>}
      </form>
      <p className="text-xs text-gray-500">Tip: use username &quot;sam&quot; and your saved password.</p>
    </main>
  );
}


