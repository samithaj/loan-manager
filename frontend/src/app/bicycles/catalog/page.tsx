"use client";

import { useState, useEffect } from "react";
import BicycleCard from "@/components/BicycleCard";
import type { Bicycle, BicycleListResponse, Branch } from "@/types/bicycle";

export default function CatalogPage() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [bicycles, setBicycles] = useState<Bicycle[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [condition, setCondition] = useState<string>("");
  const [branchId, setBranchId] = useState<string>("");
  const [brand, setBrand] = useState<string>("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const limit = 12;

  // Fetch branches
  useEffect(() => {
    async function loadBranches() {
      try {
        const res = await fetch(`${baseUrl}/public/branches`);
        if (res.ok) {
          const data = await res.json();
          setBranches(data.data || []);
        }
      } catch (err) {
        console.error("Failed to load branches:", err);
      }
    }
    loadBranches();
  }, [baseUrl]);

  // Fetch bicycles
  useEffect(() => {
    async function loadBicycles() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (condition) params.append("condition", condition);
        if (branchId) params.append("branch_id", branchId);
        if (brand) params.append("brand", brand);
        if (minPrice) params.append("min_price", minPrice);
        if (maxPrice) params.append("max_price", maxPrice);
        if (search) params.append("search", search);
        params.append("offset", offset.toString());
        params.append("limit", limit.toString());

        const res = await fetch(`${baseUrl}/public/bicycles?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to fetch bicycles");

        const data: BicycleListResponse = await res.json();
        setBicycles(data.data || []);
        setTotal(data.total || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load bicycles");
      } finally {
        setLoading(false);
      }
    }

    loadBicycles();
  }, [baseUrl, condition, branchId, brand, minPrice, maxPrice, search, offset]);

  const resetFilters = () => {
    setCondition("");
    setBranchId("");
    setBrand("");
    setMinPrice("");
    setMaxPrice("");
    setSearch("");
    setOffset(0);
  };

  const hasFilters = condition || branchId || brand || minPrice || maxPrice || search;

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const goToPage = (page: number) => {
    setOffset((page - 1) * limit);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Browse Bicycles</h1>
          <p className="text-gray-600">
            {total} {total === 1 ? "bicycle" : "bicycles"} available for hire purchase
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                {hasFilters && (
                  <button
                    onClick={resetFilters}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Clear All
                  </button>
                )}
              </div>

              <div className="space-y-6">
                {/* Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search
                  </label>
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setOffset(0);
                    }}
                    placeholder="Search by title..."
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Condition */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Condition
                  </label>
                  <select
                    value={condition}
                    onChange={(e) => {
                      setCondition(e.target.value);
                      setOffset(0);
                    }}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Conditions</option>
                    <option value="NEW">New</option>
                    <option value="USED">Used</option>
                  </select>
                </div>

                {/* Branch */}
                {branches.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Branch
                    </label>
                    <select
                      value={branchId}
                      onChange={(e) => {
                        setBranchId(e.target.value);
                        setOffset(0);
                      }}
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">All Branches</option>
                      {branches.map((branch) => (
                        <option key={branch.id} value={branch.id}>
                          {branch.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Brand */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Brand
                  </label>
                  <input
                    type="text"
                    value={brand}
                    onChange={(e) => {
                      setBrand(e.target.value);
                      setOffset(0);
                    }}
                    placeholder="e.g., Honda, Yamaha"
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Price Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Price Range (IDR)
                  </label>
                  <div className="space-y-2">
                    <input
                      type="number"
                      value={minPrice}
                      onChange={(e) => {
                        setMinPrice(e.target.value);
                        setOffset(0);
                      }}
                      placeholder="Min price"
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <input
                      type="number"
                      value={maxPrice}
                      onChange={(e) => {
                        setMaxPrice(e.target.value);
                        setOffset(0);
                      }}
                      placeholder="Max price"
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bicycles Grid */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                <p className="mt-4 text-gray-600">Loading bicycles...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-4 text-blue-600 hover:text-blue-700 underline"
                >
                  Try Again
                </button>
              </div>
            ) : bicycles.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <svg
                  className="w-16 h-16 text-gray-400 mx-auto mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Bicycles Found</h3>
                <p className="text-gray-600 mb-4">
                  {hasFilters
                    ? "Try adjusting your filters to see more results."
                    : "No bicycles are currently available."}
                </p>
                {hasFilters && (
                  <button
                    onClick={resetFilters}
                    className="text-blue-600 hover:text-blue-700 underline"
                  >
                    Clear all filters
                  </button>
                )}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {bicycles.map((bicycle) => (
                    <BicycleCard key={bicycle.id} bicycle={bicycle} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-8 flex items-center justify-center gap-2">
                    <button
                      onClick={() => goToPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Previous
                    </button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        // Show first page, last page, current page, and pages around current
                        if (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1)
                        ) {
                          return (
                            <button
                              key={page}
                              onClick={() => goToPage(page)}
                              className={`px-4 py-2 border rounded-lg ${
                                page === currentPage
                                  ? "bg-blue-600 text-white border-blue-600"
                                  : "hover:bg-gray-50"
                              }`}
                            >
                              {page}
                            </button>
                          );
                        } else if (
                          page === currentPage - 2 ||
                          page === currentPage + 2
                        ) {
                          return <span key={page}>...</span>;
                        }
                        return null;
                      })}
                    </div>

                    <button
                      onClick={() => goToPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
