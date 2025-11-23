"use client";
import { useEffect, useState } from "react";

type PettyCashFloat = {
  id: string;
  float_name: string;
  branch_id: string;
  custodian_name: string;
  opening_balance: number;
  current_balance: number;
  reconciled_balance?: number;
  is_active: boolean;
};

type PettyCashVoucher = {
  id: string;
  voucher_number: string;
  voucher_date: string;
  voucher_type: string;
  amount: number;
  description: string;
  status: string;
  payee_name?: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function PettyCashPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [activeTab, setActiveTab] = useState<"floats" | "vouchers">("floats");
  const [floats, setFloats] = useState<PettyCashFloat[]>([]);
  const [vouchers, setVouchers] = useState<PettyCashVoucher[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "floats") {
        const res = await fetch(`${base}/v1/petty-cash/floats`, { headers: authHeaders() });
        if (res.ok) {
          const data = await res.json();
          setFloats(data.items || data || []);
        }
      } else {
        const res = await fetch(`${base}/v1/petty-cash/vouchers`, { headers: authHeaders() });
        if (res.ok) {
          const data = await res.json();
          setVouchers(data.items || data || []);
        }
      }
    } catch {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: "bg-yellow-100 text-yellow-800",
      APPROVED: "bg-green-100 text-green-800",
      REJECTED: "bg-red-100 text-red-800",
      POSTED: "bg-blue-100 text-blue-800",
      VOID: "bg-gray-100 text-gray-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  return (
    <main className="min-h-screen p-8 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Petty Cash Management</h1>
        <div className="flex gap-2">
          {activeTab === "floats" && (
            <a href="/accounting/petty-cash/floats/new" className="bg-blue-600 text-white rounded px-4 py-2">
              New Float
            </a>
          )}
          {activeTab === "vouchers" && (
            <a href="/accounting/petty-cash/vouchers/new" className="bg-blue-600 text-white rounded px-4 py-2">
              New Voucher
            </a>
          )}
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 ${activeTab === "floats" ? "border-b-2 border-blue-600 font-medium" : ""}`}
          onClick={() => setActiveTab("floats")}
        >
          Floats
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "vouchers" ? "border-b-2 border-blue-600 font-medium" : ""}`}
          onClick={() => setActiveTab("vouchers")}
        >
          Vouchers
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-sm">Loading...</div>
      ) : (
        <div className="space-y-3">
          {/* Floats Tab */}
          {activeTab === "floats" &&
            (floats.length === 0 ? (
              <div className="text-sm text-gray-500">No floats found</div>
            ) : (
              floats.map((float) => (
                <div key={float.id} className="border rounded p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium text-lg">{float.float_name}</h3>
                        {float.is_active ? (
                          <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded">ACTIVE</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">INACTIVE</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600">Custodian: {float.custodian_name}</div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500">Opening Balance</div>
                          <div className="font-medium">LKR {float.opening_balance.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-gray-500">Current Balance</div>
                          <div className="font-medium">LKR {float.current_balance.toLocaleString()}</div>
                        </div>
                        {float.reconciled_balance !== undefined && (
                          <div>
                            <div className="text-gray-500">Reconciled Balance</div>
                            <div className="font-medium">LKR {float.reconciled_balance.toLocaleString()}</div>
                            {Math.abs(float.current_balance - float.reconciled_balance) > 0.01 && (
                              <div className="text-xs text-red-600">
                                Variance: LKR {Math.abs(float.current_balance - float.reconciled_balance).toLocaleString()}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <a href={`/accounting/petty-cash/floats/${float.id}/reconcile`} className="border rounded px-3 py-1 text-sm">
                        Reconcile
                      </a>
                      <a href={`/accounting/petty-cash/floats/${float.id}/edit`} className="border rounded px-3 py-1 text-sm">
                        Edit
                      </a>
                    </div>
                  </div>
                </div>
              ))
            ))}

          {/* Vouchers Tab */}
          {activeTab === "vouchers" &&
            (vouchers.length === 0 ? (
              <div className="text-sm text-gray-500">No vouchers found</div>
            ) : (
              vouchers.map((voucher) => (
                <div key={voucher.id} className="border rounded p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm font-medium">{voucher.voucher_number}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(voucher.status)}`}>
                          {voucher.status}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            voucher.voucher_type === "RECEIPT" ? "bg-green-100 text-green-800" : "bg-orange-100 text-orange-800"
                          }`}
                        >
                          {voucher.voucher_type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">{voucher.description}</div>
                      <div className="text-sm text-gray-600">
                        Date: {voucher.voucher_date} • Amount: LKR {voucher.amount.toLocaleString()}
                        {voucher.payee_name && ` • Payee: ${voucher.payee_name}`}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <a href={`/accounting/petty-cash/vouchers/${voucher.id}`} className="border rounded px-3 py-1 text-sm">
                        View
                      </a>
                    </div>
                  </div>
                </div>
              ))
            ))}
        </div>
      )}
    </main>
  );
}
