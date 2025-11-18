"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import type { Bicycle, Branch, BicycleApplication, ApplicationResponse } from "@/types/bicycle";

export default function ApplyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [bicycles, setBicycles] = useState<Bicycle[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [applicationId, setApplicationId] = useState<string | null>(null);

  // Pre-fill from query params
  const preSelectedBicycleId = searchParams.get("bicycle_id") || "";
  const preSelectedDownPayment = searchParams.get("down_payment") || "";
  const preSelectedTenure = searchParams.get("tenure") || "36";

  // Form state
  const [formData, setFormData] = useState<BicycleApplication>({
    full_name: "",
    phone: "",
    email: "",
    nip_number: "",
    address_line1: "",
    address_line2: "",
    city: "",
    employer_name: "",
    monthly_income: undefined,
    bicycle_id: preSelectedBicycleId,
    branch_id: "",
    tenure_months: parseInt(preSelectedTenure) as 12 | 24 | 36 | 48,
    down_payment: parseFloat(preSelectedDownPayment) || 0,
  });

  // Load bicycles and branches
  useEffect(() => {
    async function loadData() {
      try {
        const [bicyclesRes, branchesRes] = await Promise.all([
          fetch(`${baseUrl}/public/bicycles?limit=100`),
          fetch(`${baseUrl}/public/branches`),
        ]);

        if (bicyclesRes.ok) {
          const data = await bicyclesRes.json();
          setBicycles(data.data || []);

          // Auto-select branch if bicycle is pre-selected
          if (preSelectedBicycleId && data.data) {
            const bicycle = data.data.find((b: Bicycle) => b.id === preSelectedBicycleId);
            if (bicycle) {
              setFormData((prev) => ({ ...prev, branch_id: bicycle.branch_id }));
            }
          }
        }

        if (branchesRes.ok) {
          const data = await branchesRes.json();
          setBranches(data.data || []);
        }
      } catch (err) {
        console.error("Failed to load data:", err);
      }
    }
    loadData();
  }, [baseUrl, preSelectedBicycleId]);

  const selectedBicycle = bicycles.find((b) => b.id === formData.bicycle_id);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Generate idempotency key
      const idempotencyKey = `app-${Date.now()}-${Math.random().toString(36).substring(7)}`;

      const res = await fetch(`${baseUrl}/v1/bicycle-applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          ...formData,
          monthly_income: formData.monthly_income ? parseFloat(formData.monthly_income.toString()) : undefined,
          down_payment: parseFloat(formData.down_payment.toString()),
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || "Failed to submit application");
      }

      const result: ApplicationResponse = await res.json();
      setApplicationId(result.id);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit application");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const monthlyPayment = selectedBicycle && formData.down_payment
    ? (selectedBicycle.hire_purchase_price - formData.down_payment) / formData.tenure_months
    : 0;

  if (success && applicationId) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h1>
            <p className="text-gray-600 mb-6">
              Your application has been successfully submitted. Our team will review it and contact you soon.
            </p>
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <div className="text-sm text-gray-600">Application ID</div>
              <div className="text-lg font-mono font-bold text-blue-600">{applicationId}</div>
            </div>
            <p className="text-sm text-gray-500 mb-6">
              Please save this application ID for your records. You will receive a confirmation email shortly.
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                href="/bicycles"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Back to Home
              </Link>
              <Link
                href="/bicycles/catalog"
                className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Browse More Bicycles
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Apply for Bicycle Finance</h1>
          <p className="text-gray-600">
            Fill out the form below to apply for hire purchase financing. All fields are required unless marked optional.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Bicycle Selection */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Bicycle</h2>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bicycle *
              </label>
              <select
                value={formData.bicycle_id}
                onChange={(e) => {
                  const bicycleId = e.target.value;
                  const bicycle = bicycles.find((b) => b.id === bicycleId);
                  setFormData({
                    ...formData,
                    bicycle_id: bicycleId,
                    branch_id: bicycle?.branch_id || "",
                    down_payment: bicycle ? bicycle.hire_purchase_price * 0.2 : 0,
                  });
                }}
                required
                className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a bicycle...</option>
                {bicycles.map((bicycle) => (
                  <option key={bicycle.id} value={bicycle.id}>
                    {bicycle.title} - {formatCurrency(bicycle.hire_purchase_price)}
                  </option>
                ))}
              </select>
            </div>

            {selectedBicycle && (
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Condition:</span>
                    <span className="ml-2 font-medium">{selectedBicycle.condition}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Cash Price:</span>
                    <span className="ml-2 font-medium">{formatCurrency(selectedBicycle.cash_price)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">HP Price:</span>
                    <span className="ml-2 font-medium">{formatCurrency(selectedBicycle.hire_purchase_price)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Branch:</span>
                    <span className="ml-2 font-medium">{selectedBicycle.branch_name || selectedBicycle.branch_id}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Finance Terms */}
          {selectedBicycle && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Finance Terms</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Down Payment (IDR) *
                  </label>
                  <input
                    type="number"
                    value={formData.down_payment}
                    onChange={(e) => setFormData({ ...formData, down_payment: parseFloat(e.target.value) || 0 })}
                    min={selectedBicycle.hire_purchase_price * 0.1}
                    max={selectedBicycle.hire_purchase_price * 0.9}
                    step={100000}
                    required
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Min: {formatCurrency(selectedBicycle.hire_purchase_price * 0.1)} (10%)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payment Period *
                  </label>
                  <select
                    value={formData.tenure_months}
                    onChange={(e) => setFormData({ ...formData, tenure_months: parseInt(e.target.value) as 12 | 24 | 36 | 48 })}
                    required
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="12">12 months</option>
                    <option value="24">24 months</option>
                    <option value="36">36 months</option>
                    <option value="48">48 months</option>
                  </select>
                </div>
              </div>

              {monthlyPayment > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Estimated Monthly Payment</div>
                  <div className="text-2xl font-bold text-blue-600">{formatCurrency(monthlyPayment)}</div>
                </div>
              )}
            </div>
          )}

          {/* Personal Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Personal Information</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  required
                  placeholder="08123456789"
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email (optional)
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  NIP Number (optional)
                </label>
                <input
                  type="text"
                  value={formData.nip_number}
                  onChange={(e) => setFormData({ ...formData, nip_number: e.target.value })}
                  placeholder="16 digits"
                  maxLength={16}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Address Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Address Information</h2>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address Line 1 *
                </label>
                <input
                  type="text"
                  value={formData.address_line1}
                  onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
                  required
                  placeholder="Street address, house number"
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address Line 2 (optional)
                </label>
                <input
                  type="text"
                  value={formData.address_line2}
                  onChange={(e) => setFormData({ ...formData, address_line2: e.target.value })}
                  placeholder="Apartment, suite, etc."
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  City *
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  required
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Employment Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Employment Information</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Employer Name (optional)
                </label>
                <input
                  type="text"
                  value={formData.employer_name}
                  onChange={(e) => setFormData({ ...formData, employer_name: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Income (IDR, optional)
                </label>
                <input
                  type="number"
                  value={formData.monthly_income || ""}
                  onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value ? parseFloat(e.target.value) : undefined })}
                  step={100000}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading || !selectedBicycle}
              className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Submitting..." : "Submit Application"}
            </button>
            <Link
              href="/bicycles/catalog"
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
            >
              Cancel
            </Link>
          </div>

          <p className="text-sm text-gray-500 text-center">
            By submitting this application, you agree to our terms and conditions and privacy policy.
          </p>
        </form>
      </div>
    </div>
  );
}
