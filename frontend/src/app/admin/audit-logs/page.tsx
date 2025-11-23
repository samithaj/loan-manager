"use client";
import { useEffect, useState } from "react";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

type AuditLog = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  username: string;
  user_id?: string;
  user_role?: string;
  timestamp: string;
  old_values?: any;
  new_values?: any;
  changes_summary?: string;
  ip_address?: string;
};

export default function AuditLogsPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  // Filters
  const [entityType, setEntityType] = useState("");
  const [action, setAction] = useState("");
  const [username, setUsername] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  // Expanded log details
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  useEffect(() => {
    loadAuditLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType, action, username, dateFrom, dateTo, offset]);

  async function loadAuditLogs() {
    setLoading(true);
    setError(null);

    try {
      const url = new URL(`${base}/v1/audit/logs`);
      if (entityType) url.searchParams.set("entity_type", entityType);
      if (action) url.searchParams.set("action", action);
      if (username) url.searchParams.set("username", username);
      if (dateFrom) url.searchParams.set("date_from", dateFrom);
      if (dateTo) url.searchParams.set("date_to", dateTo);
      url.searchParams.set("limit", limit.toString());
      url.searchParams.set("offset", offset.toString());

      const res = await fetch(url.toString(), { headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);

      const data = await res.json();
      setLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }

  function getActionColor(action: string) {
    const colors: Record<string, string> = {
      CREATE: "bg-green-100 text-green-800",
      UPDATE: "bg-blue-100 text-blue-800",
      DELETE: "bg-red-100 text-red-800",
      APPROVE: "bg-purple-100 text-purple-800",
      REJECT: "bg-orange-100 text-orange-800",
      POST: "bg-indigo-100 text-indigo-800",
      VOID: "bg-gray-100 text-gray-800",
      SUBMIT: "bg-cyan-100 text-cyan-800",
      RECONCILE: "bg-teal-100 text-teal-800",
    };
    return colors[action] || "bg-gray-100 text-gray-800";
  }

  function formatTimestamp(timestamp: string) {
    return new Date(timestamp).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function resetFilters() {
    setEntityType("");
    setAction("");
    setUsername("");
    setDateFrom("");
    setDateTo("");
    setOffset(0);
  }

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
            <p className="text-gray-600 mt-1">Track all system changes and user activities</p>
          </div>
          <a href="/dashboard" className="border rounded px-4 py-2 hover:bg-gray-50">
            ← Back to Dashboard
          </a>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Entity Type</label>
              <select
                className="border rounded px-3 py-2"
                value={entityType}
                onChange={(e) => {
                  setEntityType(e.target.value);
                  setOffset(0);
                }}
              >
                <option value="">All Types</option>
                <option value="JournalEntry">Journal Entry</option>
                <option value="PettyCashVoucher">Petty Cash Voucher</option>
                <option value="ChartOfAccounts">Chart of Accounts</option>
                <option value="CommissionRule">Commission Rule</option>
                <option value="LoanApplication">Loan Application</option>
                <option value="Customer">Customer</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Action</label>
              <select
                className="border rounded px-3 py-2"
                value={action}
                onChange={(e) => {
                  setAction(e.target.value);
                  setOffset(0);
                }}
              >
                <option value="">All Actions</option>
                <option value="CREATE">Create</option>
                <option value="UPDATE">Update</option>
                <option value="DELETE">Delete</option>
                <option value="APPROVE">Approve</option>
                <option value="REJECT">Reject</option>
                <option value="POST">Post</option>
                <option value="VOID">Void</option>
                <option value="SUBMIT">Submit</option>
                <option value="RECONCILE">Reconcile</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Username</label>
              <input
                type="text"
                className="border rounded px-3 py-2"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setOffset(0);
                }}
                placeholder="Filter by username"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">From Date</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setOffset(0);
                }}
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">To Date</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setOffset(0);
                }}
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                className="border rounded px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 flex-1"
                onClick={loadAuditLogs}
                disabled={loading}
              >
                {loading ? "Loading..." : "Search"}
              </button>
              <button
                className="border rounded px-4 py-2 hover:bg-gray-50"
                onClick={resetFilters}
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg">{error}</div>}

        {/* Results */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Showing {logs.length} of {total} audit logs
            </div>
            {totalPages > 1 && (
              <div className="flex gap-2">
                <button
                  className="border rounded px-3 py-1 text-sm disabled:opacity-50"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                >
                  Previous
                </button>
                <span className="px-3 py-1 text-sm">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  className="border rounded px-3 py-1 text-sm disabled:opacity-50"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset(offset + limit)}
                >
                  Next
                </button>
              </div>
            )}
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading audit logs...</div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No audit logs found</div>
          ) : (
            <div className="divide-y">
              {logs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs px-2 py-1 rounded font-medium ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{log.entity_type}</span>
                        <span className="text-xs text-gray-500">ID: {log.entity_id.substring(0, 8)}...</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mb-1">
                        <span>👤 {log.username}</span>
                        {log.user_role && <span className="text-xs">({log.user_role})</span>}
                        <span>🕐 {formatTimestamp(log.timestamp)}</span>
                        {log.ip_address && <span className="text-xs">IP: {log.ip_address}</span>}
                      </div>
                      {log.changes_summary && (
                        <div className="text-sm text-gray-700 mt-2 p-2 bg-gray-50 rounded">
                          {log.changes_summary}
                        </div>
                      )}
                    </div>
                    <button
                      className="text-sm text-blue-600 hover:text-blue-800"
                      onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                    >
                      {expandedLog === log.id ? "Hide Details" : "Show Details"}
                    </button>
                  </div>

                  {/* Expanded details */}
                  {expandedLog === log.id && (
                    <div className="mt-4 pt-4 border-t space-y-3">
                      {log.old_values && (
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">Previous Values:</div>
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(log.old_values, null, 2)}
                          </pre>
                        </div>
                      )}
                      {log.new_values && (
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">New Values:</div>
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(log.new_values, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
