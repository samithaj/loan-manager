"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import BikeTransferFlow from "@/components/BikeTransferFlow";
import BikeStatusBadge from "@/components/BikeStatusBadge";

interface Transfer {
  id: string;
  bicycle_id: string;
  from_branch_id: string;
  to_branch_id: string;
  status: "PENDING" | "APPROVED" | "IN_TRANSIT" | "COMPLETED" | "REJECTED" | "CANCELLED";
  requested_by: string;
  requested_at: string;
  approved_by?: string;
  approved_at?: string;
  in_transit_at?: string;
  completed_by?: string;
  completed_at?: string;
  rejected_by?: string;
  rejected_at?: string;
  rejection_reason?: string;
  notes?: string;
  bicycle?: {
    id: string;
    title: string;
    current_stock_number?: string;
  };
}

export default function TransfersPage() {
  const searchParams = useSearchParams();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const preSelectedBikeId = searchParams.get("bike_id");

  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"pending" | "in_transit" | "history">("pending");
  const [showNewTransferModal, setShowNewTransferModal] = useState(!!preSelectedBikeId);
  const [selectedTransfer, setSelectedTransfer] = useState<Transfer | null>(null);

  // New transfer form
  const [newTransferForm, setNewTransferForm] = useState({
    bicycle_id: preSelectedBikeId || "",
    to_branch_id: "",
    notes: ""
  });

  useEffect(() => {
    loadTransfers();
  }, [activeTab]);

  const loadTransfers = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (activeTab === "pending") params.append("status", "PENDING");
      else if (activeTab === "in_transit") params.append("status", "IN_TRANSIT,APPROVED");

      const res = await fetch(`${baseUrl}/v1/transfers?${params}`, {
        headers: { "Authorization": `Basic ${btoa("demo:demo")}` },
        credentials: "include"
      });

      if (!res.ok) throw new Error("Failed to load transfers");

      const data = await res.json();
      setTransfers(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load transfers");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const res = await fetch(`${baseUrl}/v1/bikes/${newTransferForm.bicycle_id}/transfers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}`
        },
        credentials: "include",
        body: JSON.stringify({
          to_branch_id: newTransferForm.to_branch_id,
          notes: newTransferForm.notes || undefined
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || "Failed to create transfer");
      }

      setShowNewTransferModal(false);
      setNewTransferForm({ bicycle_id: "", to_branch_id: "", notes: "" });
      loadTransfers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create transfer");
    }
  };

  const handleApprove = async (transferId: string) => {
    try {
      const res = await fetch(`${baseUrl}/v1/transfers/${transferId}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}`
        },
        credentials: "include",
        body: JSON.stringify({})
      });

      if (!res.ok) throw new Error("Failed to approve transfer");
      loadTransfers();
      setSelectedTransfer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve transfer");
    }
  };

  const handleComplete = async (transferId: string) => {
    try {
      const res = await fetch(`${baseUrl}/v1/transfers/${transferId}/complete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}`
        },
        credentials: "include",
        body: JSON.stringify({})
      });

      if (!res.ok) throw new Error("Failed to complete transfer");
      loadTransfers();
      setSelectedTransfer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to complete transfer");
    }
  };

  const handleReject = async (transferId: string, reason: string) => {
    try {
      const res = await fetch(`${baseUrl}/v1/transfers/${transferId}/reject`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}`
        },
        credentials: "include",
        body: JSON.stringify({ reason })
      });

      if (!res.ok) throw new Error("Failed to reject transfer");
      loadTransfers();
      setSelectedTransfer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject transfer");
    }
  };

  const filteredTransfers = transfers.filter((t) => {
    if (activeTab === "pending") return t.status === "PENDING";
    if (activeTab === "in_transit") return ["APPROVED", "IN_TRANSIT"].includes(t.status);
    return ["COMPLETED", "REJECTED", "CANCELLED"].includes(t.status);
  });

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Transfer Management</h1>
            <p className="text-gray-600 mt-2">Manage inter-branch bike transfers</p>
          </div>
          <button
            onClick={() => setShowNewTransferModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Transfer Request
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab("pending")}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === "pending"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                }`}
              >
                Pending Approval
              </button>
              <button
                onClick={() => setActiveTab("in_transit")}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === "in_transit"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                }`}
              >
                In Transit
              </button>
              <button
                onClick={() => setActiveTab("history")}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === "history"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
                }`}
              >
                History
              </button>
            </nav>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : filteredTransfers.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>No {activeTab === "history" ? "transfer history" : `${activeTab.replace("_", " ")} transfers`}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredTransfers.map((transfer) => (
                  <div
                    key={transfer.id}
                    className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                    onClick={() => setSelectedTransfer(transfer)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-gray-900">
                            {transfer.from_branch_id} → {transfer.to_branch_id}
                          </h3>
                          <BikeStatusBadge status={transfer.status} size="sm" />
                        </div>
                        {transfer.bicycle && (
                          <p className="text-sm text-gray-600">
                            Bike: {transfer.bicycle.title}
                            {transfer.bicycle.current_stock_number && (
                              <span className="ml-2 font-mono text-xs">
                                {transfer.bicycle.current_stock_number}
                              </span>
                            )}
                          </p>
                        )}
                        <p className="text-sm text-gray-600 mt-1">
                          Requested by {transfer.requested_by} on{" "}
                          {new Date(transfer.requested_at).toLocaleDateString("en-LK")}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {transfer.status === "PENDING" && (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleApprove(transfer.id);
                              }}
                              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                            >
                              Approve
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const reason = prompt("Rejection reason:");
                                if (reason) handleReject(transfer.id, reason);
                              }}
                              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {["APPROVED", "IN_TRANSIT"].includes(transfer.status) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleComplete(transfer.id);
                            }}
                            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                          >
                            Mark Completed
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Transfer Modal */}
      {showNewTransferModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">New Transfer Request</h3>
            <form onSubmit={handleCreateTransfer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bike ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTransferForm.bicycle_id}
                  onChange={(e) => setNewTransferForm({ ...newTransferForm, bicycle_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Bike ID"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To Branch <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTransferForm.to_branch_id}
                  onChange={(e) => setNewTransferForm({ ...newTransferForm, to_branch_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., WW, HP, BRC"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={newTransferForm.notes}
                  onChange={(e) => setNewTransferForm({ ...newTransferForm, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Reason for transfer"
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowNewTransferModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Create Transfer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Transfer Detail Modal */}
      {selectedTransfer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Transfer Details</h3>
              <button
                onClick={() => setSelectedTransfer(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <BikeTransferFlow transfer={selectedTransfer} />
          </div>
        </div>
      )}
    </div>
  );
}
