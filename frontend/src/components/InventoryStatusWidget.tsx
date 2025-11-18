"use client";

import { useEffect, useState } from "react";

interface InventoryStats {
  [status: string]: number;
}

export default function InventoryStatusWidget() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await fetch(`${baseUrl}/v1/reports/bicycleInventory`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          // Aggregate by status
          const statsMap: InventoryStats = {};
          let totalValue = 0;

          data.data.forEach((item: any) => {
            if (!statsMap[item.status]) {
              statsMap[item.status] = 0;
            }
            statsMap[item.status] += item.count;
            totalValue += parseFloat(item.total_value || 0);
          });

          setStats({ ...statsMap, total_value: totalValue });
        }
      } catch (error) {
        console.error("Failed to load inventory stats:", error);
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [baseUrl]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Inventory Status</h2>
        <div className="text-center py-8 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const totalValue = stats.total_value || 0;
  delete stats.total_value;

  const totalCount = Object.values(stats).reduce((sum, count) => sum + count, 0);

  const statusColors: Record<string, string> = {
    AVAILABLE: "text-green-600 bg-green-100",
    RESERVED: "text-yellow-600 bg-yellow-100",
    SOLD: "text-gray-600 bg-gray-100",
    MAINTENANCE: "text-red-600 bg-red-100",
  };

  const statusIcons: Record<string, string> = {
    AVAILABLE: "✓",
    RESERVED: "⏱",
    SOLD: "✓",
    MAINTENANCE: "🔧",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Inventory Status</h2>
        <a href="/inventory" className="text-sm text-blue-600 hover:text-blue-700">
          View All →
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {Object.entries(stats).map(([status, count]) => (
          <div
            key={status}
            className={`p-3 rounded-lg ${statusColors[status] || "text-gray-600 bg-gray-100"}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl">{statusIcons[status] || "•"}</span>
              <span className="text-2xl font-bold">{count}</span>
            </div>
            <div className="text-xs font-medium mt-1">{status}</div>
          </div>
        ))}
      </div>

      <div className="pt-4 border-t">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-600">Total Inventory</span>
          <span className="text-lg font-bold text-gray-900">{totalCount}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Total Value</span>
          <span className="text-sm font-semibold text-gray-900">{formatCurrency(totalValue)}</span>
        </div>
      </div>
    </div>
  );
}
