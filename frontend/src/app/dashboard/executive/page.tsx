"use client";
import { useEffect, useState } from "react";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

type KPIData = {
  period: {
    from: string;
    to: string;
  };
  financial: {
    total_revenue: number;
    total_expenses: number;
    net_profit: number;
    profit_margin: number;
  };
  journal_entries: {
    posted_count: number;
    draft_count: number;
    total_count: number;
  };
  petty_cash: {
    total_approved: number;
    total_pending: number;
    total_rejected: number;
  };
  commissions: {
    total_amount: number;
    total_transactions: number;
  };
};

type AccountingSummary = {
  accounts_by_category: Record<string, number>;
  journal_entries_by_status: Record<string, number>;
  petty_cash_vouchers_by_status: Record<string, number>;
};

export default function ExecutiveDashboardPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [accountingSummary, setAccountingSummary] = useState<AccountingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Date range filters - default to current month
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const [dateFrom, setDateFrom] = useState(firstDay.toISOString().split("T")[0]);
  const [dateTo, setDateTo] = useState(today.toISOString().split("T")[0]);

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo]);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);

    try {
      // Load executive KPIs
      const kpiUrl = new URL(`${base}/v1/analytics/executive-dashboard`);
      kpiUrl.searchParams.set("date_from", dateFrom);
      kpiUrl.searchParams.set("date_to", dateTo);

      const kpiRes = await fetch(kpiUrl.toString(), { headers: authHeaders() });
      if (!kpiRes.ok) throw new Error(`KPI fetch failed: ${kpiRes.status}`);
      const kpiData = await kpiRes.json();
      setKpis(kpiData);

      // Load accounting summary
      const summaryRes = await fetch(`${base}/v1/analytics/accounting-summary`, {
        headers: authHeaders(),
      });
      if (!summaryRes.ok) throw new Error(`Summary fetch failed: ${summaryRes.status}`);
      const summaryData = await summaryRes.json();
      setAccountingSummary(summaryData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }

  function formatCurrency(amount: number) {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 2,
    }).format(amount);
  }

  function formatPercentage(value: number) {
    return `${value.toFixed(2)}%`;
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Executive Dashboard</h1>
            <p className="text-gray-600 mt-1">Key performance indicators and business metrics</p>
          </div>
          <a
            href="/dashboard"
            className="border rounded px-4 py-2 hover:bg-gray-50"
          >
            ← Back to Dashboard
          </a>
        </div>

        {/* Date Range Filter */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex gap-4 items-end">
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">From Date</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">To Date</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            <button
              className="border rounded px-4 py-2 bg-blue-600 text-white hover:bg-blue-700"
              onClick={loadDashboardData}
              disabled={loading}
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg">
            {error}
          </div>
        )}

        {loading && !kpis ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading dashboard data...</div>
          </div>
        ) : kpis ? (
          <>
            {/* Financial KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Total Revenue</div>
                <div className="text-2xl font-bold text-green-600 mt-2">
                  {formatCurrency(kpis.financial.total_revenue)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {kpis.period.from} to {kpis.period.to}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Total Expenses</div>
                <div className="text-2xl font-bold text-red-600 mt-2">
                  {formatCurrency(kpis.financial.total_expenses)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {kpis.period.from} to {kpis.period.to}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Net Profit</div>
                <div className={`text-2xl font-bold mt-2 ${
                  kpis.financial.net_profit >= 0 ? "text-green-600" : "text-red-600"
                }`}>
                  {formatCurrency(kpis.financial.net_profit)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Revenue - Expenses
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Profit Margin</div>
                <div className={`text-2xl font-bold mt-2 ${
                  kpis.financial.profit_margin >= 0 ? "text-green-600" : "text-red-600"
                }`}>
                  {formatPercentage(kpis.financial.profit_margin)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Net Profit / Revenue
                </div>
              </div>
            </div>

            {/* Journal Entries & Petty Cash */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Journal Entries */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Journal Entries</h2>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Posted Entries</span>
                    <span className="text-lg font-semibold text-green-600">
                      {kpis.journal_entries.posted_count}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Draft Entries</span>
                    <span className="text-lg font-semibold text-yellow-600">
                      {kpis.journal_entries.draft_count}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t">
                    <span className="text-sm font-medium text-gray-700">Total Entries</span>
                    <span className="text-lg font-bold">
                      {kpis.journal_entries.total_count}
                    </span>
                  </div>
                </div>
                <div className="mt-4">
                  <a
                    href="/accounting/journal-entries"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View all entries →
                  </a>
                </div>
              </div>

              {/* Petty Cash */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Petty Cash Vouchers</h2>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Approved</span>
                    <span className="text-lg font-semibold text-green-600">
                      {formatCurrency(kpis.petty_cash.total_approved)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Pending</span>
                    <span className="text-lg font-semibold text-yellow-600">
                      {formatCurrency(kpis.petty_cash.total_pending)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Rejected</span>
                    <span className="text-lg font-semibold text-red-600">
                      {formatCurrency(kpis.petty_cash.total_rejected)}
                    </span>
                  </div>
                </div>
                <div className="mt-4">
                  <a
                    href="/accounting/petty-cash"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View all vouchers →
                  </a>
                </div>
              </div>
            </div>

            {/* Commissions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Commissions Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="text-sm text-gray-600">Total Commission Amount</div>
                  <div className="text-3xl font-bold text-blue-600 mt-2">
                    {formatCurrency(kpis.commissions.total_amount)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Total Transactions</div>
                  <div className="text-3xl font-bold text-gray-900 mt-2">
                    {kpis.commissions.total_transactions}
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <a
                  href="/admin/commissions/rules"
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  View commission rules →
                </a>
              </div>
            </div>

            {/* Accounting Summary */}
            {accountingSummary && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Accounts by Category */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4">Accounts by Category</h2>
                  <div className="space-y-2">
                    {Object.entries(accountingSummary.accounts_by_category).map(([category, count]) => (
                      <div key={category} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{category}</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4">
                    <a
                      href="/accounting/chart-of-accounts"
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      View chart of accounts →
                    </a>
                  </div>
                </div>

                {/* Journal Entries by Status */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4">Journal Entry Status</h2>
                  <div className="space-y-2">
                    {Object.entries(accountingSummary.journal_entries_by_status).map(([status, count]) => (
                      <div key={status} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{status}</span>
                        <span className={`font-semibold ${
                          status === "POSTED" ? "text-green-600" :
                          status === "DRAFT" ? "text-yellow-600" :
                          "text-red-600"
                        }`}>
                          {count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Petty Cash Vouchers by Status */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4">Petty Cash Status</h2>
                  <div className="space-y-2">
                    {Object.entries(accountingSummary.petty_cash_vouchers_by_status).map(([status, count]) => (
                      <div key={status} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{status}</span>
                        <span className={`font-semibold ${
                          status === "APPROVED" ? "text-green-600" :
                          status === "PENDING" ? "text-yellow-600" :
                          status === "REJECTED" ? "text-red-600" :
                          "text-gray-600"
                        }`}>
                          {count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </main>
  );
}
