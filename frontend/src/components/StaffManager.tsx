"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type Staff = { id: string; name: string; role: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function StaffManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<Staff>({ id: "", name: "", role: "" });
  const [editingId, setEditingId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/staff`, { cache: "no-store", headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Staff[];
      setRows(data);
    } catch (e) {
      setError("Failed to load staff");
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
    const payload = { id: form.id || `S${Date.now()}`, name: form.name, role: form.role };
    const isEdit = !!editingId;
    const url = isEdit ? `${base}/v1/staff/${editingId}` : `${base}/v1/staff`;
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
    const saved = (await res.json()) as Staff;
    setRows((prev) => {
      const others = prev.filter((s) => s.id !== saved.id);
      return [...others, saved].sort((a, b) => a.id.localeCompare(b.id));
    });
    setForm({ id: "", name: "", role: "" });
    setEditingId(null);
  }

  async function onDelete(id: string) {
    if (!confirm(`Delete staff ${id}?`)) return;
    const res = await fetch(`${base}/v1/staff/${id}`, { method: "DELETE", headers: authHeaders() });
    if (!res.ok) {
      setError(`Delete failed (${res.status})`);
      return;
    }
    setRows((prev) => prev.filter((s) => s.id !== id));
  }

  function onEdit(s: Staff) {
    setEditingId(s.id);
    setForm({ ...s });
  }

  const cols: Column<Staff>[] = useMemo(
    () => [
      { key: "id", header: "ID" },
      { key: "name", header: "Name" },
      { key: "role", header: "Role" },
      {
        key: "id",
        header: "Actions",
        render: (s) => (
          <div className="space-x-2">
            <button className="border rounded px-2 py-0.5" onClick={() => onEdit(s)}>
              Edit
            </button>
            <button className="border rounded px-2 py-0.5" onClick={() => onDelete(s.id)}>
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
      <h2 className="font-semibold">Staff</h2>

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
        <div className="flex flex-col">
          <label className="text-xs">Role</label>
          <input
            className="border rounded px-2 py-1 bg-transparent"
            value={form.role}
            onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
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
              setForm({ id: "", name: "", role: "" });
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


