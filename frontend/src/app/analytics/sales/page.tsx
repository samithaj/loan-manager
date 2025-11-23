"use client";
import { useEffect, useState } from "react";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

type SalesAnalytics = {
  period: {
    from: string;
    to: string;
  };
  total_sales_count: number;
  total_sales_amount: number;
  average_sale_amount: number;
  sales_by_type: Record<string, { count: number; total_amount: number }>;
};

type CommissionAnalytics = {
  total_rules: number;
  active_rules: number;
  inactive_rules: number;
  rules_by_type: Record<string, number>;
  rules_by_formula: Record<string, number>;
};

export default function SalesAnalyticsPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [salesData, setSalesData] = useState<SalesAnalytics | null>(null);
  const [commissionData, setCommissionData] = useState<CommissionAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Date range filters - default to current month
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const [dateFrom, setDateFrom] = useState(firstDay.toISOString().split("T")[0]);
  const [dateTo, setDateTo] = useState(today.toISOString().split("T")[0]);
  const [branchId, setBranchId] = useState("");

  useEffect(() => {
    loadAnalyticsData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo, branchId]);

  async function loadAnalyticsData() {
    setLoading(true);
    setError(null);

    try {
      // Load sales analytics
      const salesUrl = new URL(`${base}/v1/analytics/sales`);
      salesUrl.searchParams.set("date_from", dateFrom);
      salesUrl.searchParams.set("date_to", dateTo);
      if (branchId) salesUrl.searchParams.set("branch_id", branchId);

      const salesRes = await fetch(salesUrl.toString(), { headers: authHeaders() });
      if (!salesRes.ok) throw new Error(`Sales analytics fetch failed: ${salesRes.status}`);
      const salesDataResult = await salesRes.json();
      setSalesData(salesDataResult);

      // Load commission analytics
      const commissionUrl = new URL(`${base}/v1/analytics/commissions`);
      commissionUrl.searchParams.set("date_from", dateFrom);
      commissionUrl.searchParams.set("date_to", dateTo);

      const commissionRes = await fetch(commissionUrl.toString(), { headers: authHeaders() });
      if (!commissionRes.ok) throw new Error(`Commission analytics fetch failed: ${commissionRes.status}`);
      const commissionDataResult = await commissionRes.json();
      setCommissionData(commissionDataResult);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics data");
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

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sales Analytics</h1>
            <p className="text-gray-600 mt-1">Sales performance and commission insights</p>
          </div>
          <a
            href="/dashboard"
            className="border rounded px-4 py-2 hover:bg-gray-50"
          >
            ← Back to Dashboard
          </a>
        </div>

        {/* Filters */}
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
            <div className="flex flex-col">
              <label className="text-sm font-medium mb-1">Branch ID (Optional)</label>
              <input
                type="text"
                className="border rounded px-3 py-2"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
                placeholder="Filter by branch"
              />
            </div>
            <button
              className="border rounded px-4 py-2 bg-blue-600 text-white hover:bg-blue-700"
              onClick={loadAnalyticsData}
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

        {loading && !salesData ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading analytics data...</div>
          </div>
        ) : salesData ? (
          <>
            {/* Sales Overview KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Total Sales Count</div>
                <div className="text-3xl font-bold text-blue-600 mt-2">
                  {salesData.total_sales_count}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {salesData.period.from} to {salesData.period.to}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Total Sales Amount</div>
                <div className="text-3xl font-bold text-green-600 mt-2">
                  {formatCurrency(salesData.total_sales_amount)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Revenue for period
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-600">Average Sale Amount</div>
                <div className="text-3xl font-bold text-purple-600 mt-2">
                  {formatCurrency(salesData.average_sale_amount)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Per transaction
                </div>
              </div>
            </div>

            {/* Sales by Type */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Sales Breakdown by Type</h2>
              {Object.keys(salesData.sales_by_type).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(salesData.sales_by_type).map(([type, data]) => {
                    const percentage = salesData.total_sales_amount > 0
                      ? (data.total_amount / salesData.total_sales_amount * 100)
                      : 0;

                    return (
                      <div key={type} className="border-b pb-4 last:border-b-0">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium text-gray-900">{type}</span>
                          <span className="text-sm text-gray-600">
                            {data.count} transaction{data.count !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-lg font-semibold text-green-600">
                            {formatCurrency(data.total_amount)}
                          </span>
                          <span className="text-sm font-medium text-gray-700">
                            {percentage.toFixed(1)}% of total
                          </span>
                        </div>
                        {/* Progress bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No sales data available for this period
                </div>
              )}
            </div>

            {/* Commission Analytics */}
            {commissionData && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Commission Rules Overview</h2>

                {/* Commission Rule Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-3xl font-bold text-blue-600">
                      {commissionData.total_rules}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Total Rules</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-3xl font-bold text-green-600">
                      {commissionData.active_rules}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Active Rules</div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-3xl font-bold text-gray-600">
                      {commissionData.inactive_rules}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Inactive Rules</div>
                  </div>
                </div>

                {/* Rules by Type and Formula */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Rules by Type */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Rules by Commission Type</h3>
                    <div className="space-y-2">
                      {Object.entries(commissionData.rules_by_type).map(([type, count]) => (
                        <div key={type} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm text-gray-700">{type}</span>
                          <span className="font-semibold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Rules by Formula */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Rules by Formula Type</h3>
                    <div className="space-y-2">
                      {Object.entries(commissionData.rules_by_formula).map(([formula, count]) => (
                        <div key={formula} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm text-gray-700">{formula}</span>
                          <span className="font-semibold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <a
                    href="/admin/commissions/rules"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View all commission rules →
                  </a>
                  <a
                    href="/admin/commissions/calculator"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Commission calculator →
                  </a>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a
                  href="/admin/commissions/rules/new"
                  className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-500 hover:bg-blue-50 transition"
                >
                  <div className="text-2xl mb-2">➕</div>
                  <div className="font-medium text-gray-900">Create Commission Rule</div>
                  <div className="text-xs text-gray-500 mt-1">Set up new commission structure</div>
                </a>
                <a
                  href="/admin/commissions/calculator"
                  className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-green-500 hover:bg-green-50 transition"
                >
                  <div className="text-2xl mb-2">🧮</div>
                  <div className="font-medium text-gray-900">Calculate Commission</div>
                  <div className="text-xs text-gray-500 mt-1">Test commission calculations</div>
                </a>
                <a
                  href="/dashboard/executive"
                  className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-purple-500 hover:bg-purple-50 transition"
                >
                  <div className="text-2xl mb-2">📊</div>
                  <div className="font-medium text-gray-900">Executive Dashboard</div>
                  <div className="text-xs text-gray-500 mt-1">View overall business metrics</div>
                </a>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}
