"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type Client = { id: string; displayName: string; mobile?: string | null; nationalId?: string | null; address?: string | null };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function ClientsManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<Client>({ id: "", displayName: "", mobile: "", nationalId: "", address: "" });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [q, setQ] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${base}/v1/clients`);
      if (q) url.searchParams.set("q", q);
      const res = await fetch(url.toString(), { cache: "no-store", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Client[];
      setRows(data);
    } catch {
      setError("Failed to load clients");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = {
      id: form.id || `C${Date.now()}`,
      displayName: form.displayName,
      mobile: form.mobile || undefined,
      nationalId: form.nationalId || undefined,
      address: form.address || undefined,
    };
    const isEdit = !!editingId;
    const url = isEdit ? `${base}/v1/clients/${editingId}` : `${base}/v1/clients`;
    const method = isEdit ? "PUT" : "POST";
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setError(`Save failed (${res.status})`);
      return;
    }
    const saved = (await res.json()) as Client;
    setRows((prev) => {
      const others = prev.filter((c) => c.id !== saved.id);
      return [...others, saved].sort((a, b) => a.displayName.localeCompare(b.displayName));
    });
    setForm({ id: "", displayName: "", mobile: "", nationalId: "", address: "" });
    setEditingId(null);
  }

  function onEdit(c: Client) {
    setEditingId(c.id);
    setForm({ id: c.id, displayName: c.displayName, mobile: c.mobile || "", nationalId: c.nationalId || "", address: c.address || "" });
  }

  async function onDelete(id: string) {
    if (!confirm(`Delete client ${id}?`)) return;
    const res = await fetch(`${base}/v1/clients/${id}`, { method: "DELETE", headers: authHeaders() });
    if (!res.ok) {
      setError(`Delete failed (${res.status})`);
      return;
    }
    setRows((prev) => prev.filter((c) => c.id !== id));
  }

  const cols: Column<Client>[] = useMemo(
    () => [
      { key: "id", header: "ID" },
      { key: "displayName", header: "Name" },
      { key: "mobile", header: "Mobile" },
      { key: "nationalId", header: "NIC" },
      { key: "address", header: "Address" },
      {
        key: "id",
        header: "Actions",
        render: (c) => (
          <div className="space-x-2">
            <button className="border rounded px-2 py-0.5" onClick={() => onEdit(c)}>
              Edit
            </button>
            <button className="border rounded px-2 py-0.5" onClick={() => onDelete(c.id)}>
              Delete
            </button>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <section className="space-y-3">
      <h2 className="font-semibold">Clients</h2>

      <div className="flex items-end gap-2">
        <div className="flex flex-col">
          <label className="text-xs">Search</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={q} onChange={(e) => setQ(e.target.value)} placeholder="name, mobile, NIC" />
        </div>
        <button className="border rounded px-3 py-1" onClick={() => load()} disabled={loading}>Refresh</button>
      </div>

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col">
          <label className="text-xs">ID</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.id} disabled={!!editingId} onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))} placeholder="(auto if empty)" />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Name</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.displayName} onChange={(e) => setForm((f) => ({ ...f, displayName: e.target.value }))} required />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Mobile</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.mobile || ""} onChange={(e) => setForm((f) => ({ ...f, mobile: e.target.value }))} />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">NIC</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.nationalId || ""} onChange={(e) => setForm((f) => ({ ...f, nationalId: e.target.value }))} />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Address</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.address || ""} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
        </div>
        <button type="submit" className="border rounded px-3 py-1" disabled={loading}>{editingId ? "Save" : "Add"}</button>
        {editingId && (
          <button type="button" className="border rounded px-3 py-1" onClick={() => { setEditingId(null); setForm({ id: "", displayName: "", mobile: "", nationalId: "", address: "" }); }}>Cancel</button>
        )}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </form>

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : (
        <PagedTable rows={rows} columns={cols} initialSort={{ key: "displayName", dir: "asc" }} />
      )}
    </section>
  );
}


