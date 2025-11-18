"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import StockNumberBadge from "@/components/StockNumberBadge";
import BikeStatusBadge from "@/components/BikeStatusBadge";
import BikeCostSummary from "@/components/BikeCostSummary";
import BikeLifecycleTimeline from "@/components/BikeLifecycleTimeline";

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
  business_model?: string;
  base_purchase_price?: number;
  selling_price?: number;
  profit_or_loss?: number;
  procurement_date?: string;
  procured_by?: string;
  supplier_name?: string;
  procurement_notes?: string;
  condition?: string;
  mileage_km?: number;
  color?: string;
  thumbnail_url?: string;
  image_urls: string[];
}

interface StockAssignment {
  full_stock_number: string;
  branch_id: string;
  assigned_date: string;
  assigned_by: string;
  reason: string;
  notes?: string;
  released_date?: string;
}

interface Transfer {
  id: string;
  from_branch_id: string;
  to_branch_id: string;
  status: string;
  requested_by: string;
  requested_at: string;
  approved_at?: string;
  completed_at?: string;
}

export default function BikeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bikeId = params.id as string;
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [bike, setBike] = useState<Bike | null>(null);
  const [costSummary, setCostSummary] = useState<any>(null);
  const [stockHistory, setStockHistory] = useState<StockAssignment[]>([]);
  const [transferHistory, setTransferHistory] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "cost" | "stock" | "transfers">("overview");

  useEffect(() => {
    loadBikeData();
  }, [bikeId]);

  const loadBikeData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load bike details
      const bikeRes = await fetch(`${baseUrl}/v1/bikes/${bikeId}`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (!bikeRes.ok) throw new Error("Failed to load bike details");
      const bikeData = await bikeRes.json();
      setBike(bikeData);

      // Load cost summary
      const costRes = await fetch(`${baseUrl}/v1/bikes/${bikeId}/cost-summary`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (costRes.ok) {
        const costData = await costRes.json();
        setCostSummary(costData);
      }

      // Load stock history
      const stockRes = await fetch(`${baseUrl}/v1/bikes/${bikeId}/stock-history`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (stockRes.ok) {
        const stockData = await stockRes.json();
        setStockHistory(stockData.assignments || []);
      }

      // Load transfer history
      const transferRes = await fetch(`${baseUrl}/v1/bikes/${bikeId}/transfer-history`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (transferRes.ok) {
        const transferData = await transferRes.json();
        setTransferHistory(transferData.transfers || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bike data");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !bike) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-red-900 mb-2">Error Loading Bike</h2>
            <p className="text-red-700">{error || "Bike not found"}</p>
            <Link
              href="/bikes/inventory"
              className="inline-block mt-4 text-blue-600 hover:text-blue-800"
            >
              ← Back to Inventory
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const imageUrl = bike.thumbnail_url || bike.image_urls[0] || "/placeholder-bicycle.png";
  const fullImageUrl = imageUrl.startsWith("http") ? imageUrl : `${baseUrl}${imageUrl}`;

  // Convert data to timeline events
  const timelineEvents = [];

  if (bike.procurement_date) {
    timelineEvents.push({
      id: "procurement",
      type: "PROCUREMENT" as const,
      title: "Bike Procured",
      description: `Purchased from ${bike.supplier_name || "supplier"}`,
      date: bike.procurement_date,
      user: bike.procured_by,
      details: bike.base_purchase_price ? { purchase_price: bike.base_purchase_price } : {}
    });
  }

  stockHistory.forEach((assignment, index) => {
    timelineEvents.push({
      id: `stock-${index}`,
      type: "STOCK_ASSIGNMENT" as const,
      title: `Stock Number Assigned`,
      description: `${assignment.full_stock_number} at ${assignment.branch_id}`,
      date: assignment.assigned_date,
      user: assignment.assigned_by,
      details: { reason: assignment.reason }
    });
  });

  transferHistory.forEach((transfer) => {
    timelineEvents.push({
      id: `transfer-${transfer.id}`,
      type: "TRANSFER" as const,
      title: "Transfer",
      description: `${transfer.from_branch_id} → ${transfer.to_branch_id}`,
      date: transfer.requested_at,
      user: transfer.requested_by,
      details: { status: transfer.status }
    });
  });

  timelineEvents.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link href="/bikes/inventory" className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block">
            ← Back to Inventory
          </Link>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-3 gap-6">
          {/* Left Column - Image and Basic Info */}
          <div className="col-span-1">
            <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
              <div className="relative h-64 bg-gray-100">
                <img
                  src={fullImageUrl}
                  alt={bike.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = "/placeholder-bicycle.png";
                  }}
                />
              </div>
              <div className="p-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{bike.title}</h1>
                <p className="text-gray-600 mb-4">
                  {bike.brand} {bike.model} ({bike.year})
                </p>

                <div className="space-y-2 mb-4">
                  {bike.current_stock_number && (
                    <StockNumberBadge stockNumber={bike.current_stock_number} size="lg" />
                  )}
                  <BikeStatusBadge status={bike.status} size="lg" />
                </div>

                <div className="pt-4 border-t space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Company:</span>
                    <span className="font-medium">{bike.company_id}</span>
                  </div>
                  {bike.current_branch_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Current Branch:</span>
                      <span className="font-medium">{bike.current_branch_id}</span>
                    </div>
                  )}
                  {bike.business_model && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Business Model:</span>
                      <span className="font-medium">{bike.business_model.replace(/_/g, " ")}</span>
                    </div>
                  )}
                  {bike.condition && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Condition:</span>
                      <span className="font-medium">{bike.condition}</span>
                    </div>
                  )}
                  {bike.mileage_km !== null && bike.mileage_km !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Mileage:</span>
                      <span className="font-medium">{bike.mileage_km.toLocaleString()} km</span>
                    </div>
                  )}
                  {bike.color && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Color:</span>
                      <span className="font-medium">{bike.color}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="pt-4 mt-4 border-t space-y-2">
                  {bike.status === "IN_STOCK" && (
                    <>
                      <Link
                        href={`/bikes/transfers?bike_id=${bike.id}`}
                        className="block w-full text-center bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium"
                      >
                        Transfer Bike
                      </Link>
                      <Link
                        href={`/bikes/sales?bike_id=${bike.id}`}
                        className="block w-full text-center bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
                      >
                        Record Sale
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Tabs */}
          <div className="col-span-2">
            {/* Tabs */}
            <div className="bg-white rounded-lg shadow-md mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === "overview"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                    }`}
                  >
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab("cost")}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === "cost"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                    }`}
                  >
                    Cost Summary
                  </button>
                  <button
                    onClick={() => setActiveTab("stock")}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === "stock"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                    }`}
                  >
                    Stock History
                  </button>
                  <button
                    onClick={() => setActiveTab("transfers")}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === "transfers"
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                    }`}
                  >
                    Transfers
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {/* Overview Tab */}
                {activeTab === "overview" && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Procurement Details</h3>
                      <dl className="grid grid-cols-2 gap-4 text-sm">
                        {bike.procurement_date && (
                          <div>
                            <dt className="text-gray-600">Procurement Date</dt>
                            <dd className="font-medium text-gray-900">
                              {new Date(bike.procurement_date).toLocaleDateString("en-LK")}
                            </dd>
                          </div>
                        )}
                        {bike.procured_by && (
                          <div>
                            <dt className="text-gray-600">Procured By</dt>
                            <dd className="font-medium text-gray-900">{bike.procured_by}</dd>
                          </div>
                        )}
                        {bike.supplier_name && (
                          <div>
                            <dt className="text-gray-600">Supplier</dt>
                            <dd className="font-medium text-gray-900">{bike.supplier_name}</dd>
                          </div>
                        )}
                        {bike.base_purchase_price !== null && bike.base_purchase_price !== undefined && (
                          <div>
                            <dt className="text-gray-600">Purchase Price</dt>
                            <dd className="font-medium text-gray-900">
                              {formatCurrency(bike.base_purchase_price)}
                            </dd>
                          </div>
                        )}
                      </dl>
                      {bike.procurement_notes && (
                        <div className="mt-4">
                          <dt className="text-sm text-gray-600 mb-1">Notes</dt>
                          <dd className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                            {bike.procurement_notes}
                          </dd>
                        </div>
                      )}
                    </div>

                    {bike.selling_price !== null && bike.selling_price !== undefined && (
                      <div className="pt-6 border-t">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sale Information</h3>
                        <dl className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <dt className="text-gray-600">Selling Price</dt>
                            <dd className="font-medium text-gray-900">
                              {formatCurrency(bike.selling_price)}
                            </dd>
                          </div>
                          {bike.profit_or_loss !== null && bike.profit_or_loss !== undefined && (
                            <div>
                              <dt className="text-gray-600">Profit/Loss</dt>
                              <dd
                                className={`font-bold text-lg ${
                                  bike.profit_or_loss > 0
                                    ? "text-green-600"
                                    : bike.profit_or_loss < 0
                                    ? "text-red-600"
                                    : "text-gray-600"
                                }`}
                              >
                                {formatCurrency(bike.profit_or_loss)}
                              </dd>
                            </div>
                          )}
                        </dl>
                      </div>
                    )}
                  </div>
                )}

                {/* Cost Summary Tab */}
                {activeTab === "cost" && costSummary && (
                  <BikeCostSummary costSummary={costSummary} />
                )}

                {/* Stock History Tab */}
                {activeTab === "stock" && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Stock Number Assignments</h3>
                    {stockHistory.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No stock assignments yet</p>
                    ) : (
                      <div className="space-y-3">
                        {stockHistory.map((assignment, index) => (
                          <div
                            key={index}
                            className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <StockNumberBadge
                                  stockNumber={assignment.full_stock_number}
                                  size="md"
                                />
                                <p className="text-sm text-gray-600 mt-2">
                                  Branch: <span className="font-medium">{assignment.branch_id}</span>
                                </p>
                              </div>
                              <div className="text-right text-xs text-gray-500">
                                {new Date(assignment.assigned_date).toLocaleDateString("en-LK")}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600">
                              <p>Assigned by: {assignment.assigned_by}</p>
                              <p>Reason: {assignment.reason}</p>
                              {assignment.notes && <p className="mt-1 text-gray-500">{assignment.notes}</p>}
                              {assignment.released_date && (
                                <p className="mt-2 text-orange-600">
                                  Released on {new Date(assignment.released_date).toLocaleDateString("en-LK")}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Transfers Tab */}
                {activeTab === "transfers" && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Transfer History</h3>
                    {transferHistory.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No transfers yet</p>
                    ) : (
                      <div className="space-y-3">
                        {transferHistory.map((transfer) => (
                          <div
                            key={transfer.id}
                            className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <p className="font-medium text-gray-900">
                                  {transfer.from_branch_id} → {transfer.to_branch_id}
                                </p>
                                <p className="text-sm text-gray-600 mt-1">
                                  Status:{" "}
                                  <span className="font-medium">{transfer.status.replace(/_/g, " ")}</span>
                                </p>
                              </div>
                              <div className="text-right text-xs text-gray-500">
                                {new Date(transfer.requested_at).toLocaleDateString("en-LK")}
                              </div>
                            </div>
                            <p className="text-sm text-gray-600">Requested by: {transfer.requested_by}</p>
                            {transfer.completed_at && (
                              <p className="text-sm text-green-600 mt-1">
                                Completed on {new Date(transfer.completed_at).toLocaleDateString("en-LK")}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Timeline */}
            <BikeLifecycleTimeline events={timelineEvents} />
          </div>
        </div>
      </div>
    </div>
  );
}
