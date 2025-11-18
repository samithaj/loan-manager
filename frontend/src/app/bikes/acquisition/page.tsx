"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface ProcurementFormData {
  company_id: string;
  branch_id: string;
  business_model: "HIRE_PURCHASE" | "SECOND_HAND_SALE";
  title: string;
  brand: string;
  model: string;
  year: number;
  base_purchase_price: number;
  procurement_date: string;
  procured_by: string;
  supplier_name?: string;
  supplier_contact?: string;
  procurement_invoice_number?: string;
  procurement_notes?: string;
  condition?: "NEW" | "USED";
  mileage_km?: number;
  color?: string;
}

export default function BikeAcquisitionPage() {
  const router = useRouter();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [formData, setFormData] = useState<ProcurementFormData>({
    company_id: "MA",
    branch_id: "",
    business_model: "SECOND_HAND_SALE",
    title: "",
    brand: "",
    model: "",
    year: new Date().getFullYear(),
    base_purchase_price: 0,
    procurement_date: new Date().toISOString().split("T")[0],
    procured_by: "",
    condition: "USED",
    mileage_km: 0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [createdBikeId, setCreatedBikeId] = useState<string | null>(null);
  const [stockNumber, setStockNumber] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${baseUrl}/v1/bikes/procure`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${btoa("demo:demo")}` // Replace with actual auth
        },
        credentials: "include",
        body: JSON.stringify({
          ...formData,
          year: parseInt(formData.year.toString()),
          base_purchase_price: parseFloat(formData.base_purchase_price.toString()),
          mileage_km: formData.mileage_km ? parseInt(formData.mileage_km.toString()) : undefined
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || errorData.detail || "Failed to procure bike");
      }

      const data = await res.json();
      setCreatedBikeId(data.bicycle.id);
      setStockNumber(data.stock_number);
      setSuccess(true);

      // Reset form after 2 seconds
      setTimeout(() => {
        router.push(`/bikes/${data.bicycle.id}`);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to procure bike");
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

  if (success && stockNumber) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Bike Procured Successfully!</h2>
            <p className="text-gray-600 mb-4">Stock Number: <span className="font-mono font-bold text-lg">{stockNumber}</span></p>
            <p className="text-sm text-gray-500 mb-6">Redirecting to bike details...</p>
            {createdBikeId && (
              <Link
                href={`/bikes/${createdBikeId}`}
                className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                View Bike Details
              </Link>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/bikes/inventory" className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block">
            ← Back to Inventory
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Bike Procurement</h1>
          <p className="text-gray-600 mt-2">
            Register a new bike purchase and automatically assign a stock number
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-red-600 mr-3 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h3 className="text-sm font-semibold text-red-900">Error</h3>
                <p className="text-sm text-red-800 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
          {/* Business Details */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Business Details</h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.company_id}
                  onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="MA">MA - Monaragala</option>
                  <option value="IN">IN - Badulla</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Branch <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.branch_id}
                  onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., WW, HP, BRC"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Model <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.business_model}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      business_model: e.target.value as "HIRE_PURCHASE" | "SECOND_HAND_SALE"
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="SECOND_HAND_SALE">Second-hand Sale</option>
                  <option value="HIRE_PURCHASE">Hire Purchase</option>
                </select>
              </div>
            </div>
          </div>

          {/* Bike Details */}
          <div className="mb-6 pt-6 border-t">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Bike Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title/Description <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Honda CB 125F Red 2020"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Brand <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Honda"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="CB 125F"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={formData.year}
                    onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="1980"
                    max={new Date().getFullYear() + 1}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Condition
                  </label>
                  <select
                    value={formData.condition}
                    onChange={(e) =>
                      setFormData({ ...formData, condition: e.target.value as "NEW" | "USED" })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="USED">Used</option>
                    <option value="NEW">New</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mileage (km)
                  </label>
                  <input
                    type="number"
                    value={formData.mileage_km || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, mileage_km: parseInt(e.target.value) || undefined })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 25000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Color
                  </label>
                  <input
                    type="text"
                    value={formData.color || ""}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Red"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Procurement Details */}
          <div className="mb-6 pt-6 border-t">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Procurement Details</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Purchase Price (LKR) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.base_purchase_price}
                    onChange={(e) =>
                      setFormData({ ...formData, base_purchase_price: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  {formData.base_purchase_price > 0 && (
                    <p className="text-sm text-gray-600 mt-1">
                      {formatCurrency(formData.base_purchase_price)}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Procurement Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.procurement_date}
                    onChange={(e) => setFormData({ ...formData, procurement_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Procured By <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.procured_by}
                    onChange={(e) => setFormData({ ...formData, procured_by: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Staff member name"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Invoice Number
                  </label>
                  <input
                    type="text"
                    value={formData.procurement_invoice_number || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, procurement_invoice_number: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Invoice reference"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Supplier Name
                  </label>
                  <input
                    type="text"
                    value={formData.supplier_name || ""}
                    onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Supplier/seller name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Supplier Contact
                  </label>
                  <input
                    type="text"
                    value={formData.supplier_contact || ""}
                    onChange={(e) => setFormData({ ...formData, supplier_contact: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Phone or email"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Procurement Notes
                </label>
                <textarea
                  value={formData.procurement_notes || ""}
                  onChange={(e) => setFormData({ ...formData, procurement_notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Additional notes about the procurement"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-6 border-t">
            <Link
              href="/bikes/inventory"
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </Link>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? "Procuring Bike..." : "Procure Bike & Assign Stock Number"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
