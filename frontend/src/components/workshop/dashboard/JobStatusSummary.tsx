"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

interface StatusCount {
  status: string;
  count: number;
  color: string;
}

export default function JobStatusSummary() {
  const [statusCounts, setStatusCounts] = useState<StatusCount[]>([]);
  const [loading, setLoading] = useState(true);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    async function fetchJobStats() {
      try {
        const res = await fetch(`${base}/v1/workshop/jobs`, {
          credentials: "include",
        });
        if (res.ok) {
          const jobs = await res.json();

          // Count by status
          const counts: Record<string, number> = {};
          jobs.forEach((job: any) => {
            counts[job.status] = (counts[job.status] || 0) + 1;
          });

          const statusOrder = ["OPEN", "IN_PROGRESS", "COMPLETED", "INVOICED", "CANCELLED"];
          const statusColors: Record<string, string> = {
            OPEN: "bg-yellow-500",
            IN_PROGRESS: "bg-blue-500",
            COMPLETED: "bg-green-500",
            INVOICED: "bg-purple-500",
            CANCELLED: "bg-red-500",
          };

          const countsArray: StatusCount[] = statusOrder.map((status) => ({
            status,
            count: counts[status] || 0,
            color: statusColors[status],
          }));

          setStatusCounts(countsArray);
        }
      } catch (error) {
        console.error("Failed to fetch job stats:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchJobStats();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Job Pipeline</h2>
        <div className="text-center text-gray-500 py-8">Loading...</div>
      </div>
    );
  }

  const total = statusCounts.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Job Pipeline</h2>
        <Link href="/workshop/jobs" className="text-sm text-blue-600 hover:text-blue-800">
          View All →
        </Link>
      </div>

      {total === 0 ? (
        <div className="text-center text-gray-500 py-8">No jobs yet</div>
      ) : (
        <>
          {/* Visual Pipeline */}
          <div className="mb-6">
            <div className="flex gap-2 h-8 rounded-lg overflow-hidden">
              {statusCounts.map((status) => {
                const width = total > 0 ? (status.count / total) * 100 : 0;
                return width > 0 ? (
                  <div
                    key={status.status}
                    className={`${status.color} transition-all`}
                    style={{ width: `${width}%` }}
                    title={`${status.status}: ${status.count}`}
                  />
                ) : null;
              })}
            </div>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {statusCounts.map((status) => (
              <div key={status.status} className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded ${status.color}`} />
                <div className="text-xs">
                  <div className="font-medium text-gray-900">{status.count}</div>
                  <div className="text-gray-600">{status.status.replace(/_/g, " ")}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 text-center">
            <span className="text-sm text-gray-600">Total Jobs: </span>
            <span className="text-lg font-bold text-gray-900">{total}</span>
          </div>
        </>
      )}
    </div>
  );
}
