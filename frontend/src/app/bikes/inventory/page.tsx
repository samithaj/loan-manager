"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import BikeStockCard from "@/components/BikeStockCard";

interface Bike {
  id: string;
  title: string;
  brand: string;
  model: string;
  year: number;
  current_stock_number?: string;
  status: string;
  company_id: string;
  current_branch_id?: string;
  base_purchase_price?: number;
  selling_price?: number;
  profit_or_loss?: number;
  thumbnail_url?: string;
  image_urls: string[];
}

export default function BikeInventoryPage() {
  const router = useRouter();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [bikes, setBikes] = useState<Bike[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filters, setFilters] = useState({
    company_id: "",
    branch_id: "",
    status: "",
    business_model: "",
    search: ""
  });

  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const limit = 12;

  // Modal state
  const [transferModalBikeId, setTransferModalBikeId] = useState<string | null>(null);
  const [saleModalBikeId, setSaleModalBikeId] = useState<string | null>(null);

  useEffect(() => {
    loadBikes();
  }, [filters, page]);

  const loadBikes = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        skip: ((page - 1) * limit).toString(),
        limit: limit.toString()
      });

      if (filters.company_id) params.append("company_id", filters.company_id);
      if (filters.branch_id) params.append("branch_id", filters.branch_id);
      if (filters.status) params.append("status", filters.status);
      if (filters.business_model) params.append("business_model", filters.business_model);

      const res = await fetch(`${baseUrl}/v1/bikes?${params}`, {
        headers: {
          "Authorization": `Basic ${btoa("demo:demo")}` // Replace with actual auth
        },
        credentials: "include"
      });

      if (!res.ok) {
        throw new Error("Failed to load bikes");
      }

      const data = await res.json();
      setBikes(data.data || []);
      setTotalPages(Math.ceil((data.total || 0) / limit));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bikes");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    // TODO: Implement export to Excel
    alert("Export to Excel functionality coming soon!");
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Bike Inventory</h1>
            <p className="text-gray-600 mt-2">Manage second-hand bike stock and lifecycle</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleExport}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Export to Excel
            </button>
            <Link
              href="/bikes/acquisition"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Procure New Bike
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
              <select
                value={filters.company_id}
                onChange={(e) => setFilters({ ...filters, company_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Companies</option>
                <option value="MA">MA - Monaragala</option>
                <option value="IN">IN - Badulla</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
              <input
                type="text"
                value={filters.branch_id}
                onChange={(e) => setFilters({ ...filters, branch_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., WW, HP, BRC"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Statuses</option>
                <option value="IN_STOCK">In Stock</option>
                <option value="ALLOCATED">Allocated</option>
                <option value="IN_TRANSIT">In Transit</option>
                <option value="SOLD">Sold</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="WRITTEN_OFF">Written Off</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Model</label>
              <select
                value={filters.business_model}
                onChange={(e) => setFilters({ ...filters, business_model: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Models</option>
                <option value="SECOND_HAND_SALE">Second-hand Sale</option>
                <option value="HIRE_PURCHASE">Hire Purchase</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilters({
                    company_id: "",
                    branch_id: "",
                    status: "",
                    business_model: "",
                    search: ""
                  });
                  setPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!loading && bikes.length === 0 && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg
              className="w-16 h-16 text-gray-400 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No bikes found</h3>
            <p className="text-gray-600 mb-4">
              {Object.values(filters).some((v) => v)
                ? "Try adjusting your filters"
                : "Get started by procuring your first bike"}
            </p>
            {!Object.values(filters).some((v) => v) && (
              <Link
                href="/bikes/acquisition"
                className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Procure New Bike
              </Link>
            )}
          </div>
        )}

        {/* Bikes Grid */}
        {!loading && bikes.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              {bikes.map((bike) => (
                <BikeStockCard
                  key={bike.id}
                  bike={bike}
                  showActions={true}
                  onTransfer={(id) => setTransferModalBikeId(id)}
                  onSell={(id) => setSaleModalBikeId(id)}
                  onView={(id) => router.push(`/bikes/${id}`)}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}

        {/* Transfer Modal - Placeholder */}
        {transferModalBikeId && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md">
              <h3 className="text-lg font-semibold mb-4">Transfer Bike</h3>
              <p className="text-gray-600 mb-4">
                Transfer functionality will be available in the Transfer Management page.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setTransferModalBikeId(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  Close
                </button>
                <Link
                  href="/bikes/transfers"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Go to Transfers
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Sale Modal - Placeholder */}
        {saleModalBikeId && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md">
              <h3 className="text-lg font-semibold mb-4">Record Sale</h3>
              <p className="text-gray-600 mb-4">
                Sale functionality will be available in the Sales page.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setSaleModalBikeId(null)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  Close
                </button>
                <Link
                  href="/bikes/sales"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Go to Sales
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
