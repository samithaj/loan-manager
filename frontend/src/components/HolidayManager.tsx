"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type Holiday = { id: string; name: string; date: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function HolidayManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<Holiday[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<Holiday>({ id: "", name: "", date: new Date().toISOString().slice(0, 10) });
  const [editingId, setEditingId] = useState<string | null>(null);

  async function load() {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${base}/v1/holidays`, { cache: "no-store", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Holiday[];
      setRows(data);
    } catch (e) {
      setError("Failed to load holidays");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = { id: form.id || `H${Date.now()}`, name: form.name, date: form.date };
    const isEdit = !!editingId;
    const url = isEdit ? `${base}/v1/holidays/${editingId}` : `${base}/v1/holidays`;
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
    // optimistic update
    const saved = (await res.json()) as Holiday;
    setRows((prev) => {
      const others = prev.filter((h) => h.id !== saved.id);
      return [...others, saved].sort((a, b) => a.date.localeCompare(b.date));
    });
    setForm({ id: "", name: "", date: new Date().toISOString().slice(0, 10) });
    setEditingId(null);
  }

  async function onDelete(id: string) {
    if (!confirm(`Delete holiday ${id}?`)) return;
    const res = await fetch(`${base}/v1/holidays/${id}`, { method: "DELETE", headers: authHeaders() });
    if (!res.ok) {
      setError(`Delete failed (${res.status})`);
      return;
    }
    setRows((prev) => prev.filter((h) => h.id !== id));
  }

  function onEdit(h: Holiday) {
    setEditingId(h.id);
    setForm({ ...h });
  }

  const cols: Column<Holiday>[] = useMemo(
    () => [
      { key: "id", header: "ID" },
      { key: "name", header: "Name" },
      { key: "date", header: "Date" },
      {
        key: "id",
        header: "Actions",
        render: (h) => (
          <div className="space-x-2">
            <button className="border rounded px-2 py-0.5" onClick={() => onEdit(h)}>Edit</button>
            <button className="border rounded px-2 py-0.5" onClick={() => onDelete(h.id)}>Delete</button>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <section className="space-y-3">
      <h2 className="font-semibold">Holidays</h2>

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col">
          <label className="text-xs">ID</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.id} disabled={!!editingId} onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))} placeholder="(auto if empty)" />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Name</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Date</label>
          <input type="date" className="border rounded px-2 py-1 bg-transparent" value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))} required />
        </div>
        <button type="submit" className="border rounded px-3 py-1" disabled={loading}>{editingId ? "Save" : "Add"}</button>
        {editingId && (
          <button type="button" className="border rounded px-3 py-1" onClick={() => { setEditingId(null); setForm({ id: "", name: "", date: new Date().toISOString().slice(0,10) }); }}>Cancel</button>
        )}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </form>

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : (
        <PagedTable rows={rows} columns={cols} initialSort={{ key: "date", dir: "asc" }} />
      )}
    </section>
  );
}



