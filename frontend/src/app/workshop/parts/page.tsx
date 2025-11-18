"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Part {
  id: string;
  part_code: string;
  name: string;
  description?: string;
  category: string;
  brand?: string;
  unit: string;
  is_universal: boolean;
  minimum_stock_level: number;
  reorder_point: number;
  is_active: boolean;
  created_at: string;
}

interface StockSummary {
  part_id: string;
  part_code: string;
  part_name: string;
  category: string;
  branch_id: string;
  total_quantity: number;
  average_cost: number;
  total_value: number;
  below_minimum: boolean;
}

export default function PartsInventoryPage() {
  const [parts, setParts] = useState<Part[]>([]);
  const [stockSummary, setStockSummary] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    category: "",
    search: "",
    activeOnly: true
  });
  const [viewMode, setViewMode] = useState<"parts" | "stock">("stock");

  useEffect(() => {
    if (viewMode === "parts") {
      fetchParts();
    } else {
      fetchStockSummary();
    }
  }, [filter, viewMode]);

  const fetchParts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.category) params.append("category", filter.category);
      if (filter.search) params.append("search", filter.search);
      if (filter.activeOnly) params.append("active_only", "true");

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/workshop/parts?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setParts(data.items || []);
      }
    } catch (error) {
      console.error("Error fetching parts:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStockSummary = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.category) params.append("category", filter.category);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/workshop/parts/summary?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setStockSummary(data || []);
      }
    } catch (error) {
      console.error("Error fetching stock summary:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD"
    }).format(amount);
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      ENGINE: "bg-red-100 text-red-800",
      BRAKE: "bg-orange-100 text-orange-800",
      TYRE: "bg-yellow-100 text-yellow-800",
      ELECTRICAL: "bg-blue-100 text-blue-800",
      SUSPENSION: "bg-indigo-100 text-indigo-800",
      TRANSMISSION: "bg-purple-100 text-purple-800",
      FLUIDS: "bg-green-100 text-green-800",
      CONSUMABLES: "bg-gray-100 text-gray-800"
    };
    return colors[category] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Parts Inventory</h1>
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode("stock")}
            className={`px-4 py-2 rounded-lg transition ${
              viewMode === "stock"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            Stock Summary
          </button>
          <button
            onClick={() => setViewMode("parts")}
            className={`px-4 py-2 rounded-lg transition ${
              viewMode === "parts"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
          >
            Parts Catalog
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filter.category}
              onChange={(e) => setFilter({ ...filter, category: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="ENGINE">Engine</option>
              <option value="BRAKE">Brake</option>
              <option value="TYRE">Tyre</option>
              <option value="ELECTRICAL">Electrical</option>
              <option value="SUSPENSION">Suspension</option>
              <option value="TRANSMISSION">Transmission</option>
              <option value="EXHAUST">Exhaust</option>
              <option value="BODY">Body</option>
              <option value="ACCESSORIES">Accessories</option>
              <option value="FLUIDS">Fluids</option>
              <option value="CONSUMABLES">Consumables</option>
            </select>
          </div>
          {viewMode === "parts" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                value={filter.search}
                onChange={(e) => setFilter({ ...filter, search: e.target.value })}
                placeholder="Search by code, name, or brand..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading inventory...</p>
        </div>
      ) : viewMode === "stock" ? (
        /* Stock Summary View */
        stockSummary.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">No stock data found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stockSummary.map((stock) => (
              <div
                key={`${stock.part_id}-${stock.branch_id}`}
                className={`bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 ${
                  stock.below_minimum ? "border-2 border-red-500" : ""
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="font-mono text-sm text-gray-600">
                      {stock.part_code}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {stock.part_name}
                    </h3>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(
                      stock.category
                    )}`}
                  >
                    {stock.category}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xs text-gray-500">Quantity</div>
                      <div className={`text-xl font-bold ${
                        stock.below_minimum ? "text-red-600" : "text-gray-900"
                      }`}>
                        {stock.total_quantity.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Avg Cost</div>
                      <div className="text-xl font-bold text-gray-900">
                        {formatCurrency(stock.average_cost)}
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t">
                    <div className="text-xs text-gray-500">Total Value</div>
                    <div className="text-lg font-semibold text-blue-600">
                      {formatCurrency(stock.total_value)}
                    </div>
                  </div>

                  {stock.below_minimum && (
                    <div className="bg-red-50 border border-red-200 rounded p-2">
                      <div className="text-xs text-red-800 font-semibold">
                        ⚠️ Below Minimum Stock
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-600">
                    Branch: {stock.branch_id}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        /* Parts Catalog View */
        parts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">No parts found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Part Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Brand
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {parts.map((part) => (
                  <tr key={part.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono font-medium text-gray-900">
                        {part.part_code}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {part.name}
                      </div>
                      {part.description && (
                        <div className="text-xs text-gray-500 truncate max-w-xs">
                          {part.description}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getCategoryColor(
                          part.category
                        )}`}
                      >
                        {part.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {part.brand || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {part.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {part.is_universal ? (
                        <span className="text-green-600">Universal</span>
                      ) : (
                        <span className="text-gray-600">Specific</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* Summary Stats */}
      {viewMode === "stock" && stockSummary.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Inventory Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stockSummary.length}
              </div>
              <div className="text-sm text-gray-500">Total SKUs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(
                  stockSummary.reduce((sum, s) => sum + s.total_value, 0)
                )}
              </div>
              <div className="text-sm text-gray-500">Total Value</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {stockSummary.reduce((sum, s) => sum + s.total_quantity, 0).toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">Total Quantity</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {stockSummary.filter((s) => s.below_minimum).length}
              </div>
              <div className="text-sm text-gray-500">Low Stock Items</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
