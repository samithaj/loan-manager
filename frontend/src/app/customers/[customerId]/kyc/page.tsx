"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

type Guarantor = {
  id: string;
  full_name: string;
  nic: string;
  mobile: string;
  relationship: string;
  employer_name?: string;
  monthly_income?: number;
  is_primary: boolean;
  is_verified: boolean;
};

type Employment = {
  id: string;
  employer_name: string;
  job_title: string;
  employment_type: string;
  monthly_income: number;
  is_current: boolean;
  is_verified: boolean;
  start_date: string;
};

type BankAccount = {
  id: string;
  bank_name: string;
  account_number: string;
  account_type: string;
  is_primary: boolean;
  is_verified: boolean;
  status: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function CustomerKYCPage() {
  const params = useParams();
  const customerId = params?.customerId as string;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [activeTab, setActiveTab] = useState<"guarantors" | "employment" | "bank_accounts">("guarantors");
  const [guarantors, setGuarantors] = useState<Guarantor[]>([]);
  const [employment, setEmployment] = useState<Employment[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (customerId) loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, activeTab]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "guarantors") {
        const res = await fetch(`${base}/v1/customers/${customerId}/guarantors`, {
          headers: authHeaders(),
        });
        if (res.ok) setGuarantors(await res.json());
      } else if (activeTab === "employment") {
        const res = await fetch(`${base}/v1/customers/${customerId}/employment`, {
          headers: authHeaders(),
        });
        if (res.ok) setEmployment(await res.json());
      } else if (activeTab === "bank_accounts") {
        const res = await fetch(`${base}/v1/customers/${customerId}/bank-accounts`, {
          headers: authHeaders(),
        });
        if (res.ok) setBankAccounts(await res.json());
      }
    } catch (err) {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function deleteGuarantor(id: string) {
    if (!confirm("Delete this guarantor?")) return;
    try {
      const res = await fetch(`${base}/v1/guarantors/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setGuarantors((prev) => prev.filter((g) => g.id !== id));
      }
    } catch {
      setError("Delete failed");
    }
  }

  async function deleteEmployment(id: string) {
    if (!confirm("Delete this employment record?")) return;
    try {
      const res = await fetch(`${base}/v1/employment/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setEmployment((prev) => prev.filter((e) => e.id !== id));
      }
    } catch {
      setError("Delete failed");
    }
  }

  async function deleteBankAccount(id: string) {
    if (!confirm("Delete this bank account?")) return;
    try {
      const res = await fetch(`${base}/v1/customers/${customerId}/bank-accounts/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setBankAccounts((prev) => prev.filter((b) => b.id !== id));
      }
    } catch {
      setError("Delete failed");
    }
  }

  async function verifyGuarantor(id: string) {
    try {
      const res = await fetch(`${base}/v1/guarantors/${id}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        loadData();
      }
    } catch {
      setError("Verification failed");
    }
  }

  return (
    <main className="min-h-screen p-8 space-y-4">
      <h1 className="text-2xl font-semibold">Customer KYC - {customerId}</h1>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 ${
            activeTab === "guarantors" ? "border-b-2 border-blue-600 font-medium" : ""
          }`}
          onClick={() => setActiveTab("guarantors")}
        >
          Guarantors
        </button>
        <button
          className={`px-4 py-2 ${
            activeTab === "employment" ? "border-b-2 border-blue-600 font-medium" : ""
          }`}
          onClick={() => setActiveTab("employment")}
        >
          Employment
        </button>
        <button
          className={`px-4 py-2 ${
            activeTab === "bank_accounts" ? "border-b-2 border-blue-600 font-medium" : ""
          }`}
          onClick={() => setActiveTab("bank_accounts")}
        >
          Bank Accounts
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-sm">Loading...</div>
      ) : (
        <div className="space-y-4">
          {/* Guarantors Tab */}
          {activeTab === "guarantors" && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h2 className="font-medium">Guarantors ({guarantors.length})</h2>
                <a
                  href={`/customers/${customerId}/kyc/guarantors/new`}
                  className="border rounded px-3 py-1 bg-blue-600 text-white"
                >
                  Add Guarantor
                </a>
              </div>
              {guarantors.length === 0 ? (
                <div className="text-sm text-gray-500">No guarantors added</div>
              ) : (
                <div className="space-y-2">
                  {guarantors.map((g) => (
                    <div key={g.id} className="border rounded p-4 flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="font-medium">{g.full_name}</div>
                        <div className="text-sm text-gray-600">
                          {g.nic} • {g.mobile} • {g.relationship}
                        </div>
                        {g.employer_name && (
                          <div className="text-sm text-gray-600">
                            {g.employer_name} • LKR {g.monthly_income?.toLocaleString()}/mo
                          </div>
                        )}
                        <div className="flex gap-2 text-xs">
                          {g.is_primary && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded">PRIMARY</span>
                          )}
                          {g.is_verified ? (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">VERIFIED</span>
                          ) : (
                            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">UNVERIFIED</span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {!g.is_verified && (
                          <button
                            className="border rounded px-2 py-1 text-sm"
                            onClick={() => verifyGuarantor(g.id)}
                          >
                            Verify
                          </button>
                        )}
                        <a
                          href={`/customers/${customerId}/kyc/guarantors/${g.id}/edit`}
                          className="border rounded px-2 py-1 text-sm"
                        >
                          Edit
                        </a>
                        <button
                          className="border rounded px-2 py-1 text-sm text-red-600"
                          onClick={() => deleteGuarantor(g.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Employment Tab */}
          {activeTab === "employment" && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h2 className="font-medium">Employment History ({employment.length})</h2>
                <a
                  href={`/customers/${customerId}/kyc/employment/new`}
                  className="border rounded px-3 py-1 bg-blue-600 text-white"
                >
                  Add Employment
                </a>
              </div>
              {employment.length === 0 ? (
                <div className="text-sm text-gray-500">No employment records</div>
              ) : (
                <div className="space-y-2">
                  {employment.map((e) => (
                    <div key={e.id} className="border rounded p-4 flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="font-medium">
                          {e.job_title} at {e.employer_name}
                        </div>
                        <div className="text-sm text-gray-600">
                          {e.employment_type} • LKR {e.monthly_income.toLocaleString()}/mo
                        </div>
                        <div className="text-sm text-gray-600">Since {e.start_date}</div>
                        <div className="flex gap-2 text-xs">
                          {e.is_current && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded">CURRENT</span>
                          )}
                          {e.is_verified ? (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">VERIFIED</span>
                          ) : (
                            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">UNVERIFIED</span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={`/customers/${customerId}/kyc/employment/${e.id}/edit`}
                          className="border rounded px-2 py-1 text-sm"
                        >
                          Edit
                        </a>
                        <button
                          className="border rounded px-2 py-1 text-sm text-red-600"
                          onClick={() => deleteEmployment(e.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Bank Accounts Tab */}
          {activeTab === "bank_accounts" && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h2 className="font-medium">Bank Accounts ({bankAccounts.length})</h2>
                <a
                  href={`/customers/${customerId}/kyc/bank-accounts/new`}
                  className="border rounded px-3 py-1 bg-blue-600 text-white"
                >
                  Add Bank Account
                </a>
              </div>
              {bankAccounts.length === 0 ? (
                <div className="text-sm text-gray-500">No bank accounts added</div>
              ) : (
                <div className="space-y-2">
                  {bankAccounts.map((b) => (
                    <div key={b.id} className="border rounded p-4 flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="font-medium">{b.bank_name}</div>
                        <div className="text-sm text-gray-600">
                          {b.account_type} • {b.account_number}
                        </div>
                        <div className="flex gap-2 text-xs">
                          {b.is_primary && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded">PRIMARY</span>
                          )}
                          {b.status === "ACTIVE" ? (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">ACTIVE</span>
                          ) : (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-800 rounded">{b.status}</span>
                          )}
                          {b.is_verified && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded">VERIFIED</span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={`/customers/${customerId}/kyc/bank-accounts/${b.id}/edit`}
                          className="border rounded px-2 py-1 text-sm"
                        >
                          Edit
                        </a>
                        <button
                          className="border rounded px-2 py-1 text-sm text-red-600"
                          onClick={() => deleteBankAccount(b.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
