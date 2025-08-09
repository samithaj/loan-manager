"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type Office = { id: string; name: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function OfficeManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<Office[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<Office>({ id: "", name: "" });
  const [editingId, setEditingId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/offices`, { cache: "no-store", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Office[];
      setRows(data);
    } catch (e) {
      setError("Failed to load offices");
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
    const payload = { id: form.id || `O${Date.now()}`, name: form.name };
    const isEdit = !!editingId;
    const url = isEdit ? `${base}/v1/offices/${editingId}` : `${base}/v1/offices`;
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
    const saved = (await res.json()) as Office;
    setRows((prev) => {
      const others = prev.filter((o) => o.id !== saved.id);
      return [...others, saved].sort((a, b) => a.id.localeCompare(b.id));
    });
    setForm({ id: "", name: "" });
    setEditingId(null);
  }

  async function onDelete(id: string) {
    if (!confirm(`Delete office ${id}?`)) return;
    const res = await fetch(`${base}/v1/offices/${id}`, { method: "DELETE", headers: authHeaders() });
    if (!res.ok) {
      setError(`Delete failed (${res.status})`);
      return;
    }
    setRows((prev) => prev.filter((o) => o.id !== id));
  }

  function onEdit(o: Office) {
    setEditingId(o.id);
    setForm({ ...o });
  }

  const cols: Column<Office>[] = useMemo(
    () => [
      { key: "id", header: "ID" },
      { key: "name", header: "Name" },
      {
        key: "id",
        header: "Actions",
        render: (o) => (
          <div className="space-x-2">
            <button className="border rounded px-2 py-0.5" onClick={() => onEdit(o)}>
              Edit
            </button>
            <button className="border rounded px-2 py-0.5" onClick={() => onDelete(o.id)}>
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
      <h2 className="font-semibold">Offices</h2>

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col">
          <label className="text-xs">ID</label>
          <input
            className="border rounded px-2 py-1 bg-transparent"
            value={form.id}
            disabled={!!editingId}
            onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
            placeholder="(auto if empty)"
          />
        </div>
        <div className="flex flex-col">
          <label className="text-xs">Name</label>
          <input
            className="border rounded px-2 py-1 bg-transparent"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
        </div>
        <button type="submit" className="border rounded px-3 py-1" disabled={loading}>
          {editingId ? "Save" : "Add"}
        </button>
        {editingId && (
          <button
            type="button"
            className="border rounded px-3 py-1"
            onClick={() => {
              setEditingId(null);
              setForm({ id: "", name: "" });
            }}
          >
            Cancel
          </button>
        )}
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


