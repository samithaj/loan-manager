"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function NewGuarantorPage() {
  const params = useParams();
  const router = useRouter();
  const customerId = params?.customerId as string;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [form, setForm] = useState({
    full_name: "",
    nic: "",
    date_of_birth: "",
    mobile: "",
    email: "",
    address_line1: "",
    address_line2: "",
    city: "",
    province: "",
    postal_code: "",
    employer_name: "",
    job_title: "",
    employment_type: "PERMANENT",
    monthly_income: "",
    years_employed: "",
    relationship: "",
    is_primary: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        customer_id: customerId,
        full_name: form.full_name,
        nic: form.nic,
        date_of_birth: form.date_of_birth,
        mobile: form.mobile,
        email: form.email || undefined,
        address_line1: form.address_line1,
        address_line2: form.address_line2 || undefined,
        city: form.city,
        province: form.province || undefined,
        postal_code: form.postal_code || undefined,
        employer_name: form.employer_name || undefined,
        job_title: form.job_title || undefined,
        employment_type: form.employment_type || undefined,
        monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : undefined,
        years_employed: form.years_employed ? parseFloat(form.years_employed) : undefined,
        relationship: form.relationship,
        is_primary: form.is_primary,
      };

      const res = await fetch(`${base}/v1/customers/${customerId}/guarantors`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create guarantor");
      }

      router.push(`/customers/${customerId}/kyc`);
    } catch (err: any) {
      setError(err.message || "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="border rounded px-3 py-1"
          >
            ← Back
          </button>
          <h1 className="text-2xl font-semibold">Add Guarantor</h1>
        </div>

        {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Personal Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Full Name *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">NIC *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.nic}
                  onChange={(e) => setForm({ ...form, nic: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Date of Birth *</label>
                <input
                  type="date"
                  className="border rounded px-3 py-2"
                  value={form.date_of_birth}
                  onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Mobile *</label>
                <input
                  type="tel"
                  className="border rounded px-3 py-2"
                  value={form.mobile}
                  onChange={(e) => setForm({ ...form, mobile: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  className="border rounded px-3 py-2"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Relationship *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.relationship}
                  onChange={(e) => setForm({ ...form, relationship: e.target.value })}
                  placeholder="e.g., Spouse, Parent, Sibling"
                  required
                />
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Address</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Address Line 1 *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.address_line1}
                  onChange={(e) => setForm({ ...form, address_line1: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Address Line 2</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.address_line2}
                  onChange={(e) => setForm({ ...form, address_line2: e.target.value })}
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">City *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Province</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.province}
                  onChange={(e) => setForm({ ...form, province: e.target.value })}
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Postal Code</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.postal_code}
                  onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Employment Information */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Employment Information (Optional)</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Employer Name</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.employer_name}
                  onChange={(e) => setForm({ ...form, employer_name: e.target.value })}
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Job Title</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.job_title}
                  onChange={(e) => setForm({ ...form, job_title: e.target.value })}
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Employment Type</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.employment_type}
                  onChange={(e) => setForm({ ...form, employment_type: e.target.value })}
                >
                  <option value="PERMANENT">Permanent</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="SELF_EMPLOYED">Self Employed</option>
                  <option value="BUSINESS_OWNER">Business Owner</option>
                </select>
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Monthly Income (LKR)</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.monthly_income}
                  onChange={(e) => setForm({ ...form, monthly_income: e.target.value })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Years Employed</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.years_employed}
                  onChange={(e) => setForm({ ...form, years_employed: e.target.value })}
                  min="0"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          {/* Flags */}
          <div className="border rounded p-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_primary}
                onChange={(e) => setForm({ ...form, is_primary: e.target.checked })}
              />
              <span className="text-sm font-medium">Primary Guarantor</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded"
              disabled={loading}
            >
              {loading ? "Saving..." : "Save Guarantor"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border rounded"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
