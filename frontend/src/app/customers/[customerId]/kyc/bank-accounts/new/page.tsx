"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function NewBankAccountPage() {
  const params = useParams();
  const router = useRouter();
  const customerId = params?.customerId as string;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [form, setForm] = useState({
    bank_name: "",
    branch_name: "",
    account_number: "",
    account_type: "SAVINGS",
    account_holder_name: "",
    is_primary: false,
    is_salary_account: false,
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
        bank_name: form.bank_name,
        branch_name: form.branch_name || undefined,
        account_number: form.account_number,
        account_type: form.account_type,
        account_holder_name: form.account_holder_name,
        is_primary: form.is_primary,
        is_salary_account: form.is_salary_account,
      };

      const res = await fetch(`${base}/v1/customers/${customerId}/bank-accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create bank account");
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
          <h1 className="text-2xl font-semibold">Add Bank Account</h1>
        </div>

        {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Bank Details */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Bank Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Bank Name *</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.bank_name}
                  onChange={(e) => setForm({ ...form, bank_name: e.target.value })}
                  required
                >
                  <option value="">Select Bank</option>
                  <option value="Bank of Ceylon">Bank of Ceylon</option>
                  <option value="People's Bank">People's Bank</option>
                  <option value="Commercial Bank">Commercial Bank</option>
                  <option value="Hatton National Bank">Hatton National Bank</option>
                  <option value="Sampath Bank">Sampath Bank</option>
                  <option value="Nations Trust Bank">Nations Trust Bank</option>
                  <option value="DFCC Bank">DFCC Bank</option>
                  <option value="Pan Asia Bank">Pan Asia Bank</option>
                  <option value="Seylan Bank">Seylan Bank</option>
                  <option value="Union Bank">Union Bank</option>
                  <option value="Standard Chartered">Standard Chartered</option>
                  <option value="HSBC">HSBC</option>
                  <option value="Citibank">Citibank</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Branch Name</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.branch_name}
                  onChange={(e) => setForm({ ...form, branch_name: e.target.value })}
                  placeholder="e.g., Colombo Fort"
                />
              </div>
            </div>
          </div>

          {/* Account Information */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Account Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Account Number *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.account_number}
                  onChange={(e) => setForm({ ...form, account_number: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Account Type *</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.account_type}
                  onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                  required
                >
                  <option value="SAVINGS">Savings</option>
                  <option value="CURRENT">Current</option>
                  <option value="FIXED_DEPOSIT">Fixed Deposit</option>
                  <option value="SALARY">Salary</option>
                </select>
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Account Holder Name *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.account_holder_name}
                  onChange={(e) => setForm({ ...form, account_holder_name: e.target.value })}
                  placeholder="Name as it appears on bank statement"
                  required
                />
              </div>
            </div>
          </div>

          {/* Flags */}
          <div className="border rounded p-4 space-y-3">
            <h2 className="font-medium">Account Flags</h2>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_primary}
                onChange={(e) => setForm({ ...form, is_primary: e.target.checked })}
              />
              <span className="text-sm">
                <span className="font-medium">Primary Account</span>
                <span className="text-gray-500 ml-2">(Default account for transactions)</span>
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_salary_account}
                onChange={(e) => setForm({ ...form, is_salary_account: e.target.checked })}
              />
              <span className="text-sm">
                <span className="font-medium">Salary Account</span>
                <span className="text-gray-500 ml-2">(Used for salary deposits)</span>
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded"
              disabled={loading}
            >
              {loading ? "Saving..." : "Save Bank Account"}
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
