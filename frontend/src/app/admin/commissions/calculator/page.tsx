"use client";
import { useState } from "react";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

type CalculationResult = {
  employee_id: string;
  commission_amount: number;
  applied_rule_id?: string;
  rule_name?: string;
};

export default function CommissionCalculatorPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [form, setForm] = useState({
    commission_type: "VEHICLE_SALE",
    employee_id: "",
    employee_role: "SALES_AGENT",
    sale_amount: "",
    cost_amount: "",
    branch_id: "",
    vehicle_condition: "",
  });

  const [result, setResult] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        commission_type: form.commission_type,
        employee_id: form.employee_id,
        sale_amount: parseFloat(form.sale_amount),
        cost_amount: parseFloat(form.cost_amount),
        branch_id: form.branch_id || undefined,
        vehicle_condition: form.vehicle_condition || undefined,
      };

      const res = await fetch(`${base}/v1/commissions/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Calculation failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to calculate");
    } finally {
      setLoading(false);
    }
  }

  const profit =
    form.sale_amount && form.cost_amount
      ? parseFloat(form.sale_amount) - parseFloat(form.cost_amount)
      : 0;

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="flex items-center gap-4">
          <a href="/admin/commissions/rules" className="border rounded px-3 py-1">
            ← Back to Rules
          </a>
          <h1 className="text-2xl font-semibold">Commission Calculator</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <div className="space-y-4">
            <form onSubmit={handleCalculate} className="space-y-4">
              <div className="border rounded p-4 space-y-4">
                <h2 className="font-medium">Transaction Details</h2>
                <div className="space-y-3">
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Commission Type *</label>
                    <select
                      className="border rounded px-3 py-2"
                      value={form.commission_type}
                      onChange={(e) => setForm({ ...form, commission_type: e.target.value })}
                      required
                    >
                      <option value="VEHICLE_SALE">Vehicle Sale</option>
                      <option value="LOAN_ORIGINATION">Loan Origination</option>
                      <option value="INSURANCE_SALE">Insurance Sale</option>
                      <option value="SERVICE">Service</option>
                    </select>
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Employee ID *</label>
                    <input
                      type="text"
                      className="border rounded px-3 py-2"
                      value={form.employee_id}
                      onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                      required
                      placeholder="e.g., EMP001"
                    />
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Employee Role *</label>
                    <select
                      className="border rounded px-3 py-2"
                      value={form.employee_role}
                      onChange={(e) => setForm({ ...form, employee_role: e.target.value })}
                      required
                    >
                      <option value="SALES_AGENT">Sales Agent</option>
                      <option value="BRANCH_MANAGER">Branch Manager</option>
                      <option value="LOAN_MANAGEMENT_OFFICER">Loan Management Officer</option>
                      <option value="FINANCE_OFFICER">Finance Officer</option>
                    </select>
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Sale Amount (LKR) *</label>
                    <input
                      type="number"
                      className="border rounded px-3 py-2"
                      value={form.sale_amount}
                      onChange={(e) => setForm({ ...form, sale_amount: e.target.value })}
                      required
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Cost Amount (LKR) *</label>
                    <input
                      type="number"
                      className="border rounded px-3 py-2"
                      value={form.cost_amount}
                      onChange={(e) => setForm({ ...form, cost_amount: e.target.value })}
                      required
                      min="0"
                      step="0.01"
                    />
                  </div>
                  {profit > 0 && (
                    <div className="p-3 bg-blue-50 text-blue-900 text-sm rounded">
                      Profit: LKR {profit.toLocaleString()}
                    </div>
                  )}
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Branch ID (Optional)</label>
                    <input
                      type="text"
                      className="border rounded px-3 py-2"
                      value={form.branch_id}
                      onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                    />
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">Vehicle Condition</label>
                    <select
                      className="border rounded px-3 py-2"
                      value={form.vehicle_condition}
                      onChange={(e) => setForm({ ...form, vehicle_condition: e.target.value })}
                    >
                      <option value="">Any</option>
                      <option value="NEW">New</option>
                      <option value="USED">Used</option>
                      <option value="REFURBISHED">Refurbished</option>
                    </select>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="w-full px-6 py-3 bg-blue-600 text-white rounded font-medium"
                disabled={loading}
              >
                {loading ? "Calculating..." : "Calculate Commission"}
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="space-y-4">
            {error && (
              <div className="p-4 bg-red-50 text-red-600 rounded">
                <p className="font-medium">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {result && (
              <div className="border rounded p-6 space-y-4">
                <h2 className="font-medium text-lg">Calculation Result</h2>
                <div className="space-y-3">
                  <div className="p-4 bg-green-50 rounded">
                    <div className="text-sm text-gray-600">Commission Amount</div>
                    <div className="text-3xl font-bold text-green-700">
                      LKR {result.commission_amount.toLocaleString()}
                    </div>
                  </div>

                  {result.applied_rule_id && (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Applied Rule:</span>
                        <span className="font-medium">{result.rule_name || result.applied_rule_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Rule ID:</span>
                        <span className="font-mono text-xs">{result.applied_rule_id}</span>
                      </div>
                    </div>
                  )}

                  {!result.applied_rule_id && (
                    <div className="p-3 bg-yellow-50 text-yellow-800 text-sm rounded">
                      No matching commission rule found. Commission amount is 0.
                    </div>
                  )}

                  <div className="pt-4 border-t space-y-2 text-sm">
                    <h3 className="font-medium">Transaction Summary</h3>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sale Amount:</span>
                      <span>LKR {parseFloat(form.sale_amount).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Cost Amount:</span>
                      <span>LKR {parseFloat(form.cost_amount).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between font-medium">
                      <span>Profit:</span>
                      <span>LKR {profit.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between font-medium text-green-700">
                      <span>Commission:</span>
                      <span>LKR {result.commission_amount.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!result && !error && (
              <div className="border rounded p-6 text-center text-gray-500">
                <p>Enter transaction details and click Calculate to see commission amount</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
