"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
};

export default function LoansPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<Partial<Loan>>({ status: "PENDING" });
  const [products, setProducts] = useState<{ id: string; name: string }[]>([]);
  const [clients, setClients] = useState<{ id: string; displayName: string }[]>([]);

  async function load() {
    setLoading(true);
    try {
      // Simple list: not yet available server-side; skip for now
      setLoans([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${base}/v1/loan-products`, { cache: "no-store", credentials: "include" });
        if (res.ok) {
          const data = (await res.json()) as { id: string; name: string }[];
          setProducts(data);
        }
      } catch { /* noop */ }
    })();
  }, [base]);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${base}/v1/clients`, { cache: "no-store", credentials: "include" });
        if (res.ok) {
          const data = (await res.json()) as { id: string; displayName: string }[];
          setClients(data);
        }
      } catch { /* noop */ }
    })();
  }, [base]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.id || !form.clientId || !form.productId || !form.principal || !form.termMonths) return;
    const res = await fetch(`${base}/v1/loans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        id: form.id,
        clientId: form.clientId,
        productId: form.productId,
        principal: Number(form.principal),
        interestRate: form.interestRate != null ? Number(form.interestRate) : null,
        termMonths: Number(form.termMonths),
        status: form.status || "PENDING",
      }),
    });
    if (res.ok) {
      const created = (await res.json()) as Loan;
      setLoans((prev) => [created, ...prev]);
      setForm({ status: "PENDING" });
    } else {
      alert("Failed to create loan");
    }
  }

  return (
    <main className="min-h-screen p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Loans</h1>

      <form onSubmit={onCreate} className="grid grid-cols-2 gap-4 max-w-2xl">
        <input className="border rounded px-3 py-2 bg-transparent" placeholder="Loan ID" value={form.id || ""} onChange={(e) => setForm({ ...form, id: e.target.value })} />
        <div>
          <select className="border rounded px-3 py-2 bg-transparent w-full" value={form.clientId || ""} onChange={(e) => setForm({ ...form, clientId: e.target.value })}>
            <option value="" disabled>Select client</option>
            {clients.sort((a,b)=>a.displayName.localeCompare(b.displayName)).map((c) => (
              <option key={c.id} value={c.id}>{c.displayName} ({c.id})</option>
            ))}
          </select>
        </div>
        <div>
          <select className="border rounded px-3 py-2 bg-transparent w-full" value={form.productId || ""} onChange={(e) => setForm({ ...form, productId: e.target.value })}>
            <option value="" disabled>Select loan product</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>{p.id} — {p.name}</option>
            ))}
          </select>
        </div>
        <input className="border rounded px-3 py-2 bg-transparent" placeholder="Principal" type="number" step="0.01" value={form.principal?.toString() || ""} onChange={(e) => setForm({ ...form, principal: Number(e.target.value) })} />
        <input className="border rounded px-3 py-2 bg-transparent" placeholder="Interest Rate (optional)" type="number" step="0.01" value={form.interestRate?.toString() || ""} onChange={(e) => setForm({ ...form, interestRate: Number(e.target.value) })} />
        <input className="border rounded px-3 py-2 bg-transparent" placeholder="Term Months" type="number" value={form.termMonths?.toString() || ""} onChange={(e) => setForm({ ...form, termMonths: Number(e.target.value) })} />
        <button className="bg-black text-white rounded px-4 py-2" type="submit">Create</button>
      </form>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Recent loans</h2>
        {loading ? (
          <div className="text-sm text-gray-500">Loading…</div>
        ) : loans.length === 0 ? (
          <div className="text-sm text-gray-500">No loans yet.</div>
        ) : (
          <ul className="list-disc pl-6">
            {loans.map((l) => (
              <li key={l.id}>
                <Link className="underline" href={`/loans/${l.id}`}>{l.id}</Link> — {l.status}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}


