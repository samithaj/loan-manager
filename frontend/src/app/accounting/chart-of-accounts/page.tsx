"use client";
import { useEffect, useState } from "react";
import { exportAccountsToCSV } from "@/lib/export";

type Account = {
  id: string;
  account_code: string;
  account_name: string;
  category: string;
  account_type: string;
  normal_balance: string;
  is_active: boolean;
  is_header: boolean;
  is_system: boolean;
  level: number;
  parent_account_id?: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function ChartOfAccountsPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState("");
  const [showInactive, setShowInactive] = useState(false);

  useEffect(() => {
    loadAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCategory, showInactive]);

  async function loadAccounts() {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${base}/v1/accounting/accounts`);
      if (filterCategory) url.searchParams.set("category", filterCategory);
      if (!showInactive) url.searchParams.set("is_active", "true");

      const res = await fetch(url.toString(), { headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setAccounts(data.items || data || []);
    } catch {
      setError("Failed to load accounts");
    } finally {
      setLoading(false);
    }
  }

  async function deleteAccount(id: string, isSystem: boolean) {
    if (isSystem) {
      alert("Cannot delete system accounts");
      return;
    }
    if (!confirm("Delete this account?")) return;
    try {
      const res = await fetch(`${base}/v1/accounting/accounts/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setAccounts((prev) => prev.filter((a) => a.id !== id));
      } else {
        const errorData = await res.json();
        alert(errorData.detail || "Delete failed");
      }
    } catch {
      setError("Delete failed");
    }
  }

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      ASSET: "bg-blue-100 text-blue-800",
      LIABILITY: "bg-red-100 text-red-800",
      EQUITY: "bg-purple-100 text-purple-800",
      REVENUE: "bg-green-100 text-green-800",
      EXPENSE: "bg-orange-100 text-orange-800",
    };
    return colors[category] || "bg-gray-100 text-gray-800";
  };

  // Group accounts by category for better display
  const accountsByCategory = accounts.reduce((acc, account) => {
    if (!acc[account.category]) {
      acc[account.category] = [];
    }
    acc[account.category].push(account);
    return acc;
  }, {} as Record<string, Account[]>);

  return (
    <main className="min-h-screen p-8 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Chart of Accounts</h1>
        <div className="flex gap-2">
          <button
            onClick={() => exportAccountsToCSV(accounts)}
            className="border rounded px-4 py-2 hover:bg-gray-50"
            disabled={accounts.length === 0}
          >
            Export CSV
          </button>
          <a
            href="/accounting/chart-of-accounts/new"
            className="bg-blue-600 text-white rounded px-4 py-2"
          >
            Add Account
          </a>
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">Category</label>
          <select
            className="border rounded px-3 py-2"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="ASSET">Assets</option>
            <option value="LIABILITY">Liabilities</option>
            <option value="EQUITY">Equity</option>
            <option value="REVENUE">Revenue</option>
            <option value="EXPENSE">Expenses</option>
          </select>
        </div>
        <label className="flex items-center gap-2 border rounded px-3 py-2">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
          />
          <span className="text-sm">Show Inactive</span>
        </label>
        <button
          className="border rounded px-4 py-2"
          onClick={() => loadAccounts()}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {/* Accounts */}
      {loading ? (
        <div className="text-sm">Loading...</div>
      ) : accounts.length === 0 ? (
        <div className="text-sm text-gray-500">No accounts found</div>
      ) : (
        <div className="space-y-6">
          {Object.entries(accountsByCategory).map(([category, categoryAccounts]) => (
            <div key={category} className="border rounded p-4">
              <h2 className="font-medium text-lg mb-3 flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(category)}`}>
                  {category}
                </span>
                <span className="text-gray-500 text-sm">({categoryAccounts.length} accounts)</span>
              </h2>
              <div className="space-y-1">
                {categoryAccounts
                  .sort((a, b) => a.account_code.localeCompare(b.account_code))
                  .map((account) => (
                    <div
                      key={account.id}
                      className={`flex justify-between items-center p-2 hover:bg-gray-50 ${
                        account.level > 0 ? `ml-${account.level * 6}` : ""
                      }`}
                      style={{ paddingLeft: `${account.level * 24 + 8}px` }}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <span className="font-mono text-sm text-gray-600 w-20">
                          {account.account_code}
                        </span>
                        <span className={`${account.is_header ? "font-medium" : ""}`}>
                          {account.account_name}
                        </span>
                        <div className="flex gap-1">
                          {account.is_header && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-200 text-gray-700 rounded">
                              HEADER
                            </span>
                          )}
                          {account.is_system && (
                            <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-800 rounded">
                              SYSTEM
                            </span>
                          )}
                          {!account.is_active && (
                            <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-800 rounded">
                              INACTIVE
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">{account.account_type}</span>
                        <span className="text-xs text-gray-500">
                          ({account.normal_balance})
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={`/accounting/chart-of-accounts/${account.id}/edit`}
                          className="border rounded px-2 py-1 text-sm"
                        >
                          Edit
                        </a>
                        {!account.is_system && (
                          <button
                            className="border rounded px-2 py-1 text-sm text-red-600"
                            onClick={() => deleteAccount(account.id, account.is_system)}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
