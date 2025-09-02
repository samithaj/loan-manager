"use client";
import { useEffect, useState } from "react";

type Collateral = {
  id: string;
  loanId?: string | null;
  type: string;
  value: number;
  details?: string | null;
};

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
  createdOn: string;
};

interface CollateralManagerProps {
  loan: Loan;
}

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function CollateralManager({ loan }: CollateralManagerProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [collaterals, setCollaterals] = useState<Collateral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCollateral, setEditingCollateral] = useState<Collateral | null>(null);
  const [form, setForm] = useState({
    type: "",
    value: "",
    details: ""
  });

  async function loadCollaterals() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loans/${loan.id}/collaterals`, {
        cache: "no-store",
        headers: authHeaders()
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Collateral[];
      setCollaterals(data);
    } catch {
      setError("Failed to load collaterals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCollaterals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loan.id]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const payload = {
      id: editingCollateral?.id || `COL${Date.now()}`,
      type: form.type,
      value: parseFloat(form.value),
      details: form.details || undefined
    };

    try {
      const method = editingCollateral ? "PUT" : "POST";
      const url = editingCollateral 
        ? `${base}/v1/loans/${loan.id}/collaterals/${editingCollateral.id}`
        : `${base}/v1/loans/${loan.id}/collaterals`;
      
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      setForm({ type: "", value: "", details: "" });
      setEditingCollateral(null);
      setShowForm(false);
      await loadCollaterals();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function onDelete(collateralId: string) {
    if (!confirm("Are you sure you want to delete this collateral?")) return;
    
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loans/${loan.id}/collaterals/${collateralId}`, {
        method: "DELETE",
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      await loadCollaterals();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function startEdit(collateral: Collateral) {
    setEditingCollateral(collateral);
    setForm({
      type: collateral.type,
      value: collateral.value.toString(),
      details: collateral.details || ""
    });
    setShowForm(true);
  }

  const collateralTypes = [
    "Vehicle",
    "Real Estate",
    "Equipment",
    "Jewelry",
    "Electronics",
    "Other"
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Collateral</h3>
        <button
          onClick={() => {
            setEditingCollateral(null);
            setForm({ type: "", value: "", details: "" });
            setShowForm(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Collateral
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-4">Loading collaterals...</div>
      ) : collaterals.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No collaterals found</div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {collaterals.map((collateral) => (
                <tr key={collateral.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {collateral.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${collateral.value.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {collateral.details || "—"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEdit(collateral)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => onDelete(collateral.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">
              {editingCollateral ? "Edit Collateral" : "Add Collateral"}
            </h3>
            
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type *
                </label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select type</option>
                  {collateralTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Value *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Details
                </label>
                <textarea
                  value={form.details}
                  onChange={(e) => setForm({ ...form, details: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingCollateral(null);
                    setForm({ type: "", value: "", details: "" });
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingCollateral ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}