"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

type Tier = {
  min: number;
  max: number | null;
  rate: number;
};

export default function NewCommissionRulePage() {
  const router = useRouter();
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [form, setForm] = useState({
    rule_name: "",
    commission_type: "VEHICLE_SALE",
    description: "",
    formula_type: "PERCENTAGE_OF_PROFIT",
    rate: "",
    tier_basis: "SALE_AMOUNT",
    min_amount: "",
    max_amount: "",
    applicable_roles: [] as string[],
    branch_id: "",
    vehicle_condition: "",
    effective_from: new Date().toISOString().split("T")[0],
    effective_until: "",
    priority: "10",
    is_active: true,
  });

  const [tiers, setTiers] = useState<Tier[]>([
    { min: 0, max: 500000, rate: 3.0 },
    { min: 500000, max: null, rate: 5.0 },
  ]);

  const [selectedRoles, setSelectedRoles] = useState<string[]>(["SALES_AGENT"]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableRoles = [
    "SALES_AGENT",
    "BRANCH_MANAGER",
    "LOAN_MANAGEMENT_OFFICER",
    "FINANCE_OFFICER",
  ];

  function toggleRole(role: string) {
    setSelectedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  }

  function addTier() {
    setTiers([...tiers, { min: 0, max: null, rate: 0 }]);
  }

  function removeTier(index: number) {
    setTiers(tiers.filter((_, i) => i !== index));
  }

  function updateTier(index: number, field: keyof Tier, value: any) {
    setTiers(
      tiers.map((tier, i) =>
        i === index ? { ...tier, [field]: value } : tier
      )
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let tierConfig = null;
      if (form.formula_type === "TIERED") {
        tierConfig = { tiers };
      }

      const payload = {
        rule_name: form.rule_name,
        commission_type: form.commission_type,
        description: form.description || undefined,
        formula_type: form.formula_type,
        rate: form.rate && form.formula_type !== "TIERED" ? parseFloat(form.rate) : undefined,
        tier_basis: form.formula_type === "TIERED" ? form.tier_basis : undefined,
        tier_configuration: tierConfig,
        min_amount: form.min_amount ? parseFloat(form.min_amount) : undefined,
        max_amount: form.max_amount ? parseFloat(form.max_amount) : undefined,
        applicable_roles: selectedRoles,
        branch_id: form.branch_id || undefined,
        vehicle_condition: form.vehicle_condition || undefined,
        effective_from: form.effective_from,
        effective_until: form.effective_until || undefined,
        priority: parseInt(form.priority),
        is_active: form.is_active,
      };

      const res = await fetch(`${base}/v1/commissions/rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create rule");
      }

      router.push("/admin/commissions/rules");
    } catch (err: any) {
      setError(err.message || "Failed to save");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="border rounded px-3 py-1">
            ← Back
          </button>
          <h1 className="text-2xl font-semibold">Create Commission Rule</h1>
        </div>

        {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Basic Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Rule Name *</label>
                <input
                  type="text"
                  className="border rounded px-3 py-2"
                  value={form.rule_name}
                  onChange={(e) => setForm({ ...form, rule_name: e.target.value })}
                  required
                />
              </div>
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
                <label className="text-sm font-medium mb-1">Priority</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: e.target.value })}
                  min="0"
                />
              </div>
              <div className="flex flex-col col-span-2">
                <label className="text-sm font-medium mb-1">Description</label>
                <textarea
                  className="border rounded px-3 py-2"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* Formula Configuration */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Formula Configuration</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Formula Type *</label>
                <select
                  className="border rounded px-3 py-2"
                  value={form.formula_type}
                  onChange={(e) => setForm({ ...form, formula_type: e.target.value })}
                  required
                >
                  <option value="FLAT_RATE">Flat Rate</option>
                  <option value="PERCENTAGE_OF_SALE">Percentage of Sale</option>
                  <option value="PERCENTAGE_OF_PROFIT">Percentage of Profit</option>
                  <option value="TIERED">Tiered</option>
                </select>
              </div>

              {form.formula_type !== "TIERED" && (
                <div className="flex flex-col">
                  <label className="text-sm font-medium mb-1">
                    Rate {form.formula_type === "FLAT_RATE" ? "(LKR)" : "(%)"} *
                  </label>
                  <input
                    type="number"
                    className="border rounded px-3 py-2"
                    value={form.rate}
                    onChange={(e) => setForm({ ...form, rate: e.target.value })}
                    step="0.01"
                    required
                  />
                </div>
              )}

              {form.formula_type === "TIERED" && (
                <div className="flex flex-col">
                  <label className="text-sm font-medium mb-1">Tier Basis *</label>
                  <select
                    className="border rounded px-3 py-2"
                    value={form.tier_basis}
                    onChange={(e) => setForm({ ...form, tier_basis: e.target.value })}
                  >
                    <option value="SALE_AMOUNT">Sale Amount</option>
                    <option value="PROFIT_AMOUNT">Profit Amount</option>
                    <option value="UNIT_COUNT">Unit Count</option>
                  </select>
                </div>
              )}

              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Min Amount (LKR)</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.min_amount}
                  onChange={(e) => setForm({ ...form, min_amount: e.target.value })}
                  step="0.01"
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Max Amount (LKR)</label>
                <input
                  type="number"
                  className="border rounded px-3 py-2"
                  value={form.max_amount}
                  onChange={(e) => setForm({ ...form, max_amount: e.target.value })}
                  step="0.01"
                />
              </div>
            </div>

            {/* Tier Configuration */}
            {form.formula_type === "TIERED" && (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-medium">Tiers</h3>
                  <button
                    type="button"
                    className="border rounded px-3 py-1 text-sm"
                    onClick={addTier}
                  >
                    Add Tier
                  </button>
                </div>
                {tiers.map((tier, index) => (
                  <div key={index} className="flex gap-2 items-center">
                    <input
                      type="number"
                      className="border rounded px-3 py-2 flex-1"
                      placeholder="Min"
                      value={tier.min}
                      onChange={(e) =>
                        updateTier(index, "min", parseFloat(e.target.value) || 0)
                      }
                    />
                    <span>to</span>
                    <input
                      type="number"
                      className="border rounded px-3 py-2 flex-1"
                      placeholder="Max (blank = unlimited)"
                      value={tier.max || ""}
                      onChange={(e) =>
                        updateTier(
                          index,
                          "max",
                          e.target.value ? parseFloat(e.target.value) : null
                        )
                      }
                    />
                    <span>@</span>
                    <input
                      type="number"
                      className="border rounded px-3 py-2 w-24"
                      placeholder="Rate %"
                      value={tier.rate}
                      onChange={(e) =>
                        updateTier(index, "rate", parseFloat(e.target.value) || 0)
                      }
                      step="0.01"
                    />
                    <span>%</span>
                    {tiers.length > 1 && (
                      <button
                        type="button"
                        className="border rounded px-2 py-1 text-red-600"
                        onClick={() => removeTier(index)}
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Applicability */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Applicability</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-2 block">Applicable Roles *</label>
                <div className="flex flex-wrap gap-2">
                  {availableRoles.map((role) => (
                    <label key={role} className="flex items-center gap-2 border rounded px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedRoles.includes(role)}
                        onChange={() => toggleRole(role)}
                      />
                      <span className="text-sm">{role.replace(/_/g, " ")}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label className="text-sm font-medium mb-1">Branch ID (Optional)</label>
                  <input
                    type="text"
                    className="border rounded px-3 py-2"
                    value={form.branch_id}
                    onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                    placeholder="Leave blank for all branches"
                  />
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-medium mb-1">Vehicle Condition</label>
                  <select
                    className="border rounded px-3 py-2"
                    value={form.vehicle_condition}
                    onChange={(e) => setForm({ ...form, vehicle_condition: e.target.value })}
                  >
                    <option value="">All</option>
                    <option value="NEW">New</option>
                    <option value="USED">Used</option>
                    <option value="REFURBISHED">Refurbished</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Effective Dates */}
          <div className="border rounded p-4 space-y-4">
            <h2 className="font-medium">Effective Dates</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Effective From *</label>
                <input
                  type="date"
                  className="border rounded px-3 py-2"
                  value={form.effective_from}
                  onChange={(e) => setForm({ ...form, effective_from: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col">
                <label className="text-sm font-medium mb-1">Effective Until</label>
                <input
                  type="date"
                  className="border rounded px-3 py-2"
                  value={form.effective_until}
                  onChange={(e) => setForm({ ...form, effective_until: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="border rounded p-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              <span className="text-sm font-medium">Active</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded"
              disabled={loading || selectedRoles.length === 0}
            >
              {loading ? "Saving..." : "Create Rule"}
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
