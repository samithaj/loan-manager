"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface LeaveBalance {
  id: string;
  user_id: string;
  leave_type_id: string;
  leave_type_name?: string;
  year: number;
  entitled_days: number;
  used_days: number;
  pending_days: number;
  remaining_days: number;
  carried_forward_days: number;
}

export default function LeaveBalancesPage() {
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchBalances();
  }, [selectedYear]);

  const fetchBalances = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave/balances?year=${selectedYear}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setBalances(data);
      } else {
        console.error("Failed to fetch leave balances");
      }
    } catch (error) {
      console.error("Error fetching leave balances:", error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return "bg-red-500";
    if (percentage >= 50) return "bg-yellow-500";
    return "bg-green-500";
  };

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i);

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Leave Balances</h1>
        <div className="flex gap-3">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <Link
            href="/hr/leaves"
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition"
          >
            View Applications
          </Link>
          <Link
            href="/hr/leaves/apply"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
          >
            Apply for Leave
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading leave balances...</p>
        </div>
      ) : balances.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">No leave balances found for {selectedYear}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {balances.map((balance) => {
            const usagePercentage =
              balance.entitled_days > 0
                ? ((balance.used_days + balance.pending_days) /
                    balance.entitled_days) *
                  100
                : 0;

            return (
              <div
                key={balance.id}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {balance.leave_type_name || balance.leave_type_id}
                  </h3>
                  <span className="text-2xl font-bold text-blue-600">
                    {balance.remaining_days}
                  </span>
                </div>

                <div className="space-y-3">
                  {/* Progress Bar */}
                  <div className="relative">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold inline-block text-gray-700">
                          Usage
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-gray-700">
                          {usagePercentage.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                      <div
                        style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                        className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${getProgressColor(
                          usagePercentage
                        )}`}
                      ></div>
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="grid grid-cols-2 gap-3 pt-3 border-t">
                    <div>
                      <div className="text-xs text-gray-500">Entitled</div>
                      <div className="text-sm font-semibold text-gray-900">
                        {balance.entitled_days} days
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Used</div>
                      <div className="text-sm font-semibold text-gray-900">
                        {balance.used_days} days
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Pending</div>
                      <div className="text-sm font-semibold text-yellow-600">
                        {balance.pending_days} days
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Remaining</div>
                      <div className="text-sm font-semibold text-green-600">
                        {balance.remaining_days} days
                      </div>
                    </div>
                  </div>

                  {balance.carried_forward_days > 0 && (
                    <div className="pt-2 border-t">
                      <div className="text-xs text-gray-500">Carried Forward</div>
                      <div className="text-sm font-semibold text-blue-600">
                        {balance.carried_forward_days} days
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary */}
      {balances.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {balances.reduce((sum, b) => sum + b.entitled_days, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Entitled</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {balances.reduce((sum, b) => sum + b.used_days, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Used</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {balances.reduce((sum, b) => sum + b.pending_days, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {balances.reduce((sum, b) => sum + b.remaining_days, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Remaining</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
