"use client";

import { useEffect, useState } from "react";

interface ApplicationStats {
  PENDING: number;
  UNDER_REVIEW: number;
  APPROVED: number;
  REJECTED: number;
  CONVERTED_TO_LOAN: number;
}

export default function ApplicationPipelineWidget() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await fetch(`${baseUrl}/v1/reports/applicationFunnel`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          // Transform data to stats format
          const statsMap: ApplicationStats = {
            PENDING: 0,
            UNDER_REVIEW: 0,
            APPROVED: 0,
            REJECTED: 0,
            CONVERTED_TO_LOAN: 0,
          };

          data.data.forEach((item: any) => {
            if (item.status in statsMap) {
              statsMap[item.status as keyof ApplicationStats] = item.count;
            }
          });

          setStats(statsMap);
        }
      } catch (error) {
        console.error("Failed to load application stats:", error);
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [baseUrl]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Pipeline</h2>
        <div className="text-center py-8 text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const total = Object.values(stats).reduce((sum, count) => sum + count, 0);
  const conversionRate = total > 0 ? ((stats.CONVERTED_TO_LOAN / total) * 100).toFixed(1) : "0";

  const statusColors: Record<keyof ApplicationStats, string> = {
    PENDING: "bg-yellow-500",
    UNDER_REVIEW: "bg-blue-500",
    APPROVED: "bg-green-500",
    REJECTED: "bg-red-500",
    CONVERTED_TO_LOAN: "bg-purple-500",
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Application Pipeline</h2>
        <a href="/applications" className="text-sm text-blue-600 hover:text-blue-700">
          View All →
        </a>
      </div>

      <div className="space-y-3">
        {Object.entries(stats).map(([status, count]) => {
          const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : "0";
          return (
            <div key={status}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-700">{status.replace(/_/g, " ")}</span>
                <span className="font-medium text-gray-900">{count}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${statusColors[status as keyof ApplicationStats]}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Conversion Rate</span>
          <span className="text-lg font-bold text-purple-600">{conversionRate}%</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {stats.CONVERTED_TO_LOAN} of {total} applications converted to loans
        </p>
      </div>
    </div>
  );
}
