"use client";

import { useEffect, useState } from "react";

interface BranchPerformance {
  branch_id: string;
  total_applications: number;
  conversions: number;
  conversion_rate: number;
}

export default function BranchPerformanceWidget() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [performance, setPerformance] = useState<BranchPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPerformance() {
      try {
        const res = await fetch(`${baseUrl}/v1/reports/branchPerformance`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setPerformance(data.data.slice(0, 5)); // Top 5 branches
        }
      } catch (error) {
        console.error("Failed to load branch performance:", error);
      } finally {
        setLoading(false);
      }
    }

    loadPerformance();
  }, [baseUrl]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Branch Performance</h2>
        <div className="text-center py-8 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (performance.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Branch Performance</h2>
        <div className="text-center py-8 text-gray-500">No data available</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Branch Performance</h2>
        <span className="text-xs text-gray-500">Top 5 Branches</span>
      </div>

      <div className="space-y-3">
        {performance.map((branch, index) => (
          <div key={branch.branch_id} className="flex items-center gap-3">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                index === 0
                  ? "bg-yellow-400 text-yellow-900"
                  : index === 1
                  ? "bg-gray-300 text-gray-700"
                  : index === 2
                  ? "bg-orange-400 text-orange-900"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              {index + 1}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-900">{branch.branch_id}</span>
                <span className="text-sm font-semibold text-green-600">
                  {branch.conversion_rate.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{branch.total_applications} applications</span>
                <span>•</span>
                <span>{branch.conversions} conversions</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t">
        <p className="text-xs text-gray-500 text-center">
          Showing top performing branches by conversion rate
        </p>
      </div>
    </div>
  );
}
