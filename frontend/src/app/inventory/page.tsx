"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { Bicycle } from "@/types/bicycle";

export default function InventoryPage() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [bicycles, setBicycles] = useState<Bicycle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [condition, setCondition] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [branchId, setBranchId] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    async function loadBicycles() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (condition) params.append("condition", condition);
        if (status) params.append("status", status);
        if (branchId) params.append("branch_id", branchId);
        if (search) params.append("search", search);
        params.append("offset", offset.toString());
        params.append("limit", limit.toString());

        const res = await fetch(`${baseUrl}/v1/bicycles?${params.toString()}`, {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch bicycles");
        }

        const data = await res.json();
        setBicycles(data.data || []);
        setTotal(data.total || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load bicycles");
      } finally {
        setLoading(false);
      }
    }

    loadBicycles();
  }, [baseUrl, condition, status, branchId, search, offset]);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      AVAILABLE: "bg-green-100 text-green-800",
      RESERVED: "bg-yellow-100 text-yellow-800",
      SOLD: "bg-gray-100 text-gray-800",
      MAINTENANCE: "bg-red-100 text-red-800",
    };
    return styles[status] || "bg-gray-100 text-gray-800";
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="min-h-screen max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Bicycle Inventory</h1>
          <p className="text-gray-600">Manage your bicycle inventory</p>
        </div>
        <Link
          href="/inventory/new"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          + Add Bicycle
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setOffset(0);
              }}
              placeholder="Search by title..."
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Condition</label>
            <select
              value={condition}
              onChange={(e) => {
                setCondition(e.target.value);
                setOffset(0);
              }}
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All</option>
              <option value="NEW">New</option>
              <option value="USED">Used</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All</option>
              <option value="AVAILABLE">Available</option>
              <option value="RESERVED">Reserved</option>
              <option value="SOLD">Sold</option>
              <option value="MAINTENANCE">Maintenance</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Branch ID</label>
            <input
              type="text"
              value={branchId}
              onChange={(e) => {
                setBranchId(e.target.value);
                setOffset(0);
              }}
              placeholder="Branch ID"
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setCondition("");
                setStatus("");
                setBranchId("");
                setSearch("");
                setOffset(0);
              }}
              className="px-4 py-2 text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Bicycles Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading bicycles...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600">{error}</p>
        </div>
      ) : bicycles.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-500 text-lg">No bicycles found</p>
          <Link
            href="/inventory/new"
            className="mt-4 inline-block text-blue-600 hover:text-blue-700 underline"
          >
            Add your first bicycle
          </Link>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Title
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Condition
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Branch
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cash Price
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bicycles.map((bicycle) => (
                    <tr key={bicycle.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-mono text-gray-900">{bicycle.id}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{bicycle.title}</div>
                        <div className="text-sm text-gray-500">
                          {bicycle.brand} {bicycle.model} ({bicycle.year})
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            bicycle.condition === "NEW"
                              ? "bg-green-100 text-green-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {bicycle.condition}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(
                            bicycle.status
                          )}`}
                        >
                          {bicycle.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{bicycle.branch_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(bicycle.cash_price)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                        <Link
                          href={`/inventory/${bicycle.id}/edit`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </Link>
                        <Link
                          href={`/bicycles/${bicycle.id}`}
                          target="_blank"
                          className="text-gray-600 hover:text-gray-900"
                        >
                          View Public
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} results
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                  disabled={offset === 0}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setOffset(offset + limit)}
                  disabled={offset + limit >= total}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
