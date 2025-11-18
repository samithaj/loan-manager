"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

type Me = { username: string; roles: string[] };

export default function Header() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`${base}/v1/me`, { credentials: "include", cache: "no-store" });
      if (res.ok) {
        const data = (await res.json()) as Me;
        setMe(data);
      } else {
        setMe(null);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const onAuth = () => load();
    window.addEventListener("auth:updated", onAuth);
    return () => window.removeEventListener("auth:updated", onAuth);
  }, []);

  async function onLogout() {
    await fetch(`${base}/v1/auth/logout`, { method: "POST", credentials: "include" });
    setMe(null);
    window.dispatchEvent(new Event("auth:updated"));
    location.href = "/login";
  }

  return (
    <header className="w-full border-b border-gray-800 bg-black/40 text-sm">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="font-semibold text-white">Loan Manager</Link>
          {me && (
            <nav className="flex items-center gap-3 text-blue-400">
              <Link href="/reference">Reference data</Link>
              <Link href="/loan-products">Loan products</Link>
              <Link href="/clients">Clients</Link>
              <Link href="/inventory">Inventory</Link>
              <Link href="/applications">Applications</Link>
            </nav>
          )}
        </div>
        <div className="flex items-center gap-3">
          {loading ? (
            <span className="text-gray-400">…</span>
          ) : me ? (
            <>
              <Link href="/profile" className="text-gray-200 underline">{me.username}</Link>
              <button onClick={onLogout} className="border rounded px-2 py-1">Logout</button>
            </>
          ) : (
            <Link href="/login" className="text-blue-400 underline">Login</Link>
          )}
        </div>
      </div>
    </header>
  );
}


