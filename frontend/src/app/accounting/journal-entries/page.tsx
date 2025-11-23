"use client";
import { useEffect, useState } from "react";

type JournalEntry = {
  id: string;
  entry_number: string;
  entry_date: string;
  entry_type: string;
  description: string;
  total_debit: number;
  total_credit: number;
  status: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function JournalEntriesPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    loadEntries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStatus]);

  async function loadEntries() {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${base}/v1/accounting/journal-entries`);
      if (filterStatus) url.searchParams.set("status", filterStatus);

      const res = await fetch(url.toString(), { headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setEntries(data.items || data || []);
    } catch {
      setError("Failed to load journal entries");
    } finally {
      setLoading(false);
    }
  }

  async function postEntry(id: string) {
    if (!confirm("Post this journal entry? This action cannot be undone.")) return;
    try {
      const res = await fetch(`${base}/v1/accounting/journal-entries/${id}/post`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        loadEntries();
      }
    } catch {
      setError("Failed to post entry");
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: "bg-yellow-100 text-yellow-800",
      POSTED: "bg-green-100 text-green-800",
      VOID: "bg-red-100 text-red-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  return (
    <main className="min-h-screen p-8 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Journal Entries</h1>
        <a
          href="/accounting/journal-entries/new"
          className="bg-blue-600 text-white rounded px-4 py-2"
        >
          New Entry
        </a>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">Status</label>
          <select
            className="border rounded px-3 py-2"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="DRAFT">Draft</option>
            <option value="POSTED">Posted</option>
            <option value="VOID">Void</option>
          </select>
        </div>
        <button className="border rounded px-4 py-2" onClick={() => loadEntries()} disabled={loading}>
          Refresh
        </button>
      </div>

      {/* Entries List */}
      {loading ? (
        <div className="text-sm">Loading...</div>
      ) : entries.length === 0 ? (
        <div className="text-sm text-gray-500">No journal entries found</div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div key={entry.id} className="border rounded p-4 flex justify-between items-start">
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-medium">{entry.entry_number}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(entry.status)}`}>
                    {entry.status}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                    {entry.entry_type.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="text-sm text-gray-600">{entry.description}</div>
                <div className="text-sm text-gray-600">
                  Date: {entry.entry_date} • Debit: LKR {entry.total_debit.toLocaleString()} • Credit: LKR{" "}
                  {entry.total_credit.toLocaleString()}
                </div>
              </div>
              <div className="flex gap-2">
                {entry.status === "DRAFT" && (
                  <button
                    className="border rounded px-3 py-1 text-sm bg-green-50 text-green-700"
                    onClick={() => postEntry(entry.id)}
                  >
                    Post
                  </button>
                )}
                <a
                  href={`/accounting/journal-entries/${entry.id}`}
                  className="border rounded px-3 py-1 text-sm"
                >
                  View
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
