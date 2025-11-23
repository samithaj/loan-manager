"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function NewEmploymentPage() {
  const params = useParams();
  const router = useRouter();
  const customerId = params?.customerId as string;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [form, setForm] = useState({
    employer_name: "",
    job_title: "",
    employment_type: "PERMANENT",
    industry: "",
    start_date: "",
    end_date: "",
    is_current: true,
    gross_income: "",
    income_frequency: "MONTHLY",
    employer_phone: "",
    employer_email: "",
    employer_address: "",
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
        employer_name: form.employer_name,
        job_title: form.job_title,
        employment_type: form.employment_type,
        industry: form.industry || undefined,
        start_date: form.start_date,
        end_date: form.is_current ? undefined : form.end_date || undefined,
        is_current: form.is_current,
        gross_income: parseFloat(form.gross_income),
        income_frequency: form.income_frequency,
        employer_phone: form.employer_phone || undefined,
        employer_email: form.employer_email || undefined,
        employer_address: form.employer_address || undefined,
      };

      const res = await fetch(`${base}/v1/customers/${customerId}/employment`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create employment record");
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
          <button onClick={() => router.back()} className="border rounded px-3 py-1">
            ← Back
          </button>
          <h1 className="text-2xl font-semibold">Add Employment Record</h1>
        </div>

        {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Employment Details */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Employment Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Employer Name *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.employer_name}
                  onChange={(e) => setForm({ ...form, employer_name: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Job Title *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.job_title}
                  onChange={(e) => setForm({ ...form, job_title: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Employment Type *</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.employment_type}
                  onChange={(e) => setForm({ ...form, employment_type: e.target.value })}
                  required
                >
                  <option value="PERMANENT">Permanent</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="SELF_EMPLOYED">Self Employed</option>
                  <option value="BUSINESS_OWNER">Business Owner</option>
                  <option value="RETIRED">Retired</option>
                  <option value="UNEMPLOYED">Unemployed</option>
                </select>
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Industry</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.industry}
                  onChange={(e) => setForm({ ...form, industry: e.target.value })}
                  placeholder="e.g., IT, Banking, Education"
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Start Date *</label>
                <input
                  type="date"
                  className="border rounded px-3 py-2"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">End Date</label>
                <input
                  type="date"
                  className="border rounded px-3 py-2"
                  value={form.end_date}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  disabled={form.is_current}
                />
              </div>
              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.is_current}
                    onChange={(e) => setForm({ ...form, is_current: e.target.checked, end_date: "" })}
                  />
                  <span className="text-sm font-medium">Currently Employed Here</span>
                </label>
              </div>
            </div>
          </div>

          {/* Income Information */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Income Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Gross Income (LKR) *</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.gross_income}
                  onChange={(e) => setForm({ ...form, gross_income: e.target.value })}
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Income Frequency *</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.income_frequency}
                  onChange={(e) => setForm({ ...form, income_frequency: e.target.value })}
                  required
                >
                  <option value="DAILY">Daily</option>
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="ANNUAL">Annual</option>
                </select>
              </div>
            </div>
          </div>

          {/* Employer Contact */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Employer Contact (Optional)</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  className="border rounded px-3 py-2"
                  value={form.employer_phone}
                  onChange={(e) => setForm({ ...form, employer_phone: e.target.value })}
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  className="border rounded px-3 py-2"
                  value={form.employer_email}
                  onChange={(e) => setForm({ ...form, employer_email: e.target.value })}
                />
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Address</label>
                <textarea
                  className="border rounded px-3 py-2"
                  value={form.employer_address}
                  onChange={(e) => setForm({ ...form, employer_address: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded"
              disabled={loading}
            >
              {loading ? "Saving..." : "Save Employment"}
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
