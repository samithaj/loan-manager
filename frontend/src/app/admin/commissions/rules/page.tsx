"use client";
import { useEffect, useState } from "react";

type CommissionRule = {
  id: string;
  rule_name: string;
  commission_type: string;
  formula_type: string;
  rate?: number;
  is_active: boolean;
  priority: number;
  applicable_roles: string[];
  effective_from: string;
  effective_until?: string;
};

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function CommissionRulesPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rules, setRules] = useState<CommissionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState("");
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  useEffect(() => {
    loadRules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterType, filterActive]);

  async function loadRules() {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${base}/v1/commissions/rules`);
      if (filterType) url.searchParams.set("commission_type", filterType);
      if (filterActive !== null) url.searchParams.set("is_active", String(filterActive));

      const res = await fetch(url.toString(), { headers: authHeaders() });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setRules(data.items || data || []);
    } catch {
      setError("Failed to load commission rules");
    } finally {
      setLoading(false);
    }
  }

  async function toggleActive(id: string, currentStatus: boolean) {
    try {
      const res = await fetch(`${base}/v1/commissions/rules/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ is_active: !currentStatus }),
      });
      if (res.ok) {
        loadRules();
      }
    } catch {
      setError("Failed to update rule");
    }
  }

  async function deleteRule(id: string) {
    if (!confirm("Delete this commission rule?")) return;
    try {
      const res = await fetch(`${base}/v1/commissions/rules/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        setRules((prev) => prev.filter((r) => r.id !== id));
      }
    } catch {
      setError("Delete failed");
    }
  }

  const formatFormulaType = (type: string) => {
    return type.replace(/_/g, " ");
  };

  return (
    <main className="min-h-screen p-8 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Commission Rules</h1>
        <div className="flex gap-2">
          <a
            href="/admin/commissions/calculator"
            className="border rounded px-4 py-2"
          >
            Calculator
          </a>
          <a
            href="/admin/commissions/rules/new"
            className="bg-blue-600 text-white rounded px-4 py-2"
          >
            Add Rule
          </a>
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">Commission Type</label>
          <select
            className="border rounded px-3 py-2"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="VEHICLE_SALE">Vehicle Sale</option>
            <option value="LOAN_ORIGINATION">Loan Origination</option>
            <option value="INSURANCE_SALE">Insurance Sale</option>
            <option value="SERVICE">Service</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">Status</label>
          <select
            className="border rounded px-3 py-2"
            value={filterActive === null ? "" : String(filterActive)}
            onChange={(e) => setFilterActive(e.target.value === "" ? null : e.target.value === "true")}
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <button
          className="border rounded px-4 py-2"
          onClick={() => loadRules()}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {/* Rules List */}
      {loading ? (
        <div className="text-sm">Loading...</div>
      ) : rules.length === 0 ? (
        <div className="text-sm text-gray-500">No commission rules found</div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="border rounded p-4 flex justify-between items-start"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium text-lg">{rule.rule_name}</h3>
                  <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                    {rule.commission_type.replace(/_/g, " ")}
                  </span>
                  {rule.is_active ? (
                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded">
                      ACTIVE
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                      INACTIVE
                    </span>
                  )}
                  <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                    Priority: {rule.priority}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Formula:</span> {formatFormulaType(rule.formula_type)}
                    {rule.rate && ` (${rule.rate}%)`}
                  </div>
                  <div>
                    <span className="font-medium">Effective:</span> {rule.effective_from}
                    {rule.effective_until && ` to ${rule.effective_until}`}
                  </div>
                  <div>
                    <span className="font-medium">Roles:</span> {rule.applicable_roles.join(", ")}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  className={`border rounded px-3 py-1 text-sm ${
                    rule.is_active ? "text-orange-600" : "text-green-600"
                  }`}
                  onClick={() => toggleActive(rule.id, rule.is_active)}
                >
                  {rule.is_active ? "Deactivate" : "Activate"}
                </button>
                <a
                  href={`/admin/commissions/rules/${rule.id}/edit`}
                  className="border rounded px-3 py-1 text-sm"
                >
                  Edit
                </a>
                <button
                  className="border rounded px-3 py-1 text-sm text-red-600"
                  onClick={() => deleteRule(rule.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
