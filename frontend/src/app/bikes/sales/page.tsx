"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import BikeSaleForm, { type SaleFormData } from "@/components/BikeSaleForm";
import StockNumberBadge from "@/components/StockNumberBadge";

interface Sale {
  id: string;
  bicycle_id: string;
  selling_price: number;
  sale_date: string;
  selling_branch_id: string;
  sold_by: string;
  customer_name: string;
  customer_contact: string;
  payment_method: string;
  profit_or_loss?: number;
  bicycle?: {
    title: string;
    current_stock_number?: string;
    brand: string;
    model: string;
  };
}

export default function SalesPage() {
  const searchParams = useSearchParams();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const preSelectedBikeId = searchParams.get("bike_id");

  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSaleModal, setShowSaleModal] = useState(!!preSelectedBikeId);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);
  const [selectedBikeId, setSelectedBikeId] = useState<string>(preSelectedBikeId || "");
  const [bikeCostSummary, setBikeCostSummary] = useState<any>(null);

  // Filters
  const [filters, setFilters] = useState({
    start_date: "",
    end_date: "",
    branch_id: ""
  });

  useEffect(() => {
    loadSales();
  }, [filters]);

  useEffect(() => {
    if (selectedBikeId && showSaleModal) {
      loadBikeCostSummary();
    }
  }, [selectedBikeId, showSaleModal]);

  const loadSales = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.start_date) params.append("start_date", filters.start_date);
      if (filters.end_date) params.append("end_date", filters.end_date);
      if (filters.branch_id) params.append("branch_id", filters.branch_id);

      const res = await fetch(`${baseUrl}/v1/sales?${params}`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (!res.ok) throw new Error("Failed to load sales");

      const data = await res.json();
      setSales(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sales");
    } finally {
      setLoading(false);
    }
  };

  const loadBikeCostSummary = async () => {
    try {
      const res = await fetch(`${baseUrl}/v1/bikes/${selectedBikeId}/cost-summary`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (res.ok) {
        const data = await res.json();
        setBikeCostSummary(data);
      }
    } catch (err) {
      console.error("Failed to load cost summary:", err);
    }
  };

  const handleRecordSale = async (saleData: SaleFormData) => {
    try {
      const res = await fetch(`${baseUrl}/v1/bikes/${saleData.bicycle_id}/sell`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}`
        },
        credentials: "include",
        body: JSON.stringify(saleData)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || "Failed to record sale");
      }

      setShowSaleModal(false);
      setSelectedBikeId("");
      setBikeCostSummary(null);
      loadSales();
    } catch (err) {
      throw err; // Re-throw to let BikeSaleForm handle it
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const totalSales = sales.reduce((sum, sale) => sum + sale.selling_price, 0);
  const totalProfit = sales.reduce((sum, sale) => sum + (sale.profit_or_loss || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sales Management</h1>
            <p className="text-gray-600 mt-2">Record and track bike sales</p>
          </div>
          <button
            onClick={() => setShowSaleModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Record Sale
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Sales</p>
                <p className="text-2xl font-bold text-gray-900">{sales.length}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalSales)}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Profit</p>
                <p className={`text-2xl font-bold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(totalProfit)}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                totalProfit >= 0 ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <svg className={`w-6 h-6 ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
              <input
                type="text"
                value={filters.branch_id}
                onChange={(e) => setFilters({ ...filters, branch_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., WW, HP"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={() => setFilters({ start_date: "", end_date: "", branch_id: "" })}
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

        {/* Sales List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Sales</h2>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : sales.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No sales recorded yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bike
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sale Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Branch
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P/L
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sales.map((sale) => (
                    <tr key={sale.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {sale.bicycle?.title || "N/A"}
                        </div>
                        {sale.bicycle?.current_stock_number && (
                          <div className="text-xs text-gray-500 font-mono">
                            {sale.bicycle.current_stock_number}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{sale.customer_name}</div>
                        <div className="text-xs text-gray-500">{sale.customer_contact}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(sale.sale_date).toLocaleDateString("en-LK")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {sale.selling_branch_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(sale.selling_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {sale.profit_or_loss !== null && sale.profit_or_loss !== undefined ? (
                          <span className={`text-sm font-semibold ${
                            sale.profit_or_loss >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {formatCurrency(sale.profit_or_loss)}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setSelectedSale(sale)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* New Sale Modal */}
      {showSaleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="my-8">
            <BikeSaleForm
              bikeId={selectedBikeId}
              totalCost={bikeCostSummary?.total_cost}
              onSubmit={handleRecordSale}
              onCancel={() => {
                setShowSaleModal(false);
                setSelectedBikeId("");
                setBikeCostSummary(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Sale Detail Modal */}
      {selectedSale && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Sale Details</h3>
              <button
                onClick={() => setSelectedSale(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-600 mb-2">Bike Information</h4>
                <p className="text-gray-900">{selectedSale.bicycle?.title}</p>
                {selectedSale.bicycle?.current_stock_number && (
                  <StockNumberBadge stockNumber={selectedSale.bicycle.current_stock_number} size="sm" className="mt-2" />
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Customer Name</h4>
                  <p className="text-gray-900">{selectedSale.customer_name}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Contact</h4>
                  <p className="text-gray-900">{selectedSale.customer_contact}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Sale Date</h4>
                  <p className="text-gray-900">{new Date(selectedSale.sale_date).toLocaleDateString("en-LK")}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Selling Branch</h4>
                  <p className="text-gray-900">{selectedSale.selling_branch_id}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Sold By</h4>
                  <p className="text-gray-900">{selectedSale.sold_by}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Payment Method</h4>
                  <p className="text-gray-900">{selectedSale.payment_method.replace(/_/g, " ")}</p>
                </div>
              </div>
              <div className="pt-4 border-t">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-1">Selling Price</h4>
                    <p className="text-xl font-bold text-gray-900">{formatCurrency(selectedSale.selling_price)}</p>
                  </div>
                  {selectedSale.profit_or_loss !== null && selectedSale.profit_or_loss !== undefined && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 mb-1">Profit/Loss</h4>
                      <p className={`text-xl font-bold ${
                        selectedSale.profit_or_loss >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(selectedSale.profit_or_loss)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
