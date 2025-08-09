"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type LoanProduct = {
  id: string;
  name: string;
  interestRate: number;
  termMonths: number;
  repaymentFrequency: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function LoanProductManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<LoanProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<LoanProduct>({ id: "", name: "", interestRate: 12, termMonths: 12, repaymentFrequency: "MONTHLY" });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loan-products`, { cache: "no-store", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as LoanProduct[];
      setRows(data);
    } catch (e) {
      setError("Failed to load loan products");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = { ...form, id: form.id || `LP${Date.now()}` };
    const res = await fetch(`${base}/v1/loan-products`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setError(`Save failed (${res.status})`);
      return;
    }
    const saved = (await res.json()) as LoanProduct;
    setRows((prev) => [...prev.filter((p) => p.id !== saved.id), saved].sort((a, b) => a.id.localeCompare(b.id)));
    setForm({ id: "", name: "", interestRate: 12, termMonths: 12, repaymentFrequency: "MONTHLY" });
  }

  const cols: Column<LoanProduct>[] = useMemo(
    () => [
      { key: "id", header: "ID" },
      { key: "name", header: "Name" },
      { key: "interestRate", header: "Interest %" },
      { key: "termMonths", header: "Term (months)" },
      { key: "repaymentFrequency", header: "Frequency" },
    ],
    []
  );

  return (
    <section className="space-y-3">
      <h2 className="font-semibold">Loan Products</h2>

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col">
          <label className="text-xs">ID</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.id} onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))} placeholder="(auto if empty)" />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Name</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Interest %</label>
          <input type="number" step="0.01" min={0} max={100} className="border rounded px-2 py-1 bg-transparent" value={form.interestRate} onChange={(e) => setForm((f) => ({ ...f, interestRate: parseFloat(e.target.value) }))} required />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Term (months)</label>
          <input type="number" min={1} className="border rounded px-2 py-1 bg-transparent" value={form.termMonths} onChange={(e) => setForm((f) => ({ ...f, termMonths: parseInt(e.target.value || "0") }))} required />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Frequency</label>
          <select className="border rounded px-2 py-1 bg-transparent" value={form.repaymentFrequency} onChange={(e) => setForm((f) => ({ ...f, repaymentFrequency: e.target.value }))}>
            <option value="DAILY">DAILY</option>
            <option value="WEEKLY">WEEKLY</option>
            <option value="BIWEEKLY">BIWEEKLY</option>
            <option value="MONTHLY">MONTHLY</option>
          </select>
        </div>
        <button type="submit" className="border rounded px-3 py-1" disabled={loading}>Add</button>
        {error && <span className="text-sm text-red-600">{error}</span>}
      </form>

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : (
        <PagedTable rows={rows} columns={cols} initialSort={{ key: "id", dir: "asc" }} />
      )}
    </section>
  );
}


