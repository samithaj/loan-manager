"use client";
import { useState, useEffect } from "react";

interface MarkupRule {
  id: number;
  name: string;
  target_type: string;
  target_value: string;
  markup_type: string;
  markup_value: number;
  is_active: boolean;
  priority: number;
}

export default function MarkupRulesPage() {
  const [rules, setRules] = useState<MarkupRule[]>([]);
  const [loading, setLoading] = useState(true);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const res = await fetch(`${base}/v1/workshop/markup-rules`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setRules(data);
      }
    } catch (error) {
      console.error("Failed to fetch markup rules:", error);
    } finally {
      setLoading(false);
    }
  };

  const targetTypeColors: Record<string, string> = {
    PART_CATEGORY: "bg-blue-100 text-blue-800",
    LABOUR: "bg-green-100 text-green-800",
    OVERHEAD: "bg-yellow-100 text-yellow-800",
    BIKE_SALE: "bg-purple-100 text-purple-800",
    DEFAULT: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Markup Rules</h1>
          <p className="text-gray-600 mt-1">
            Configure pricing markup rules for parts, labour, and bike sales
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          Create Rule
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading rules...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Target Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Target Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Markup
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{rule.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        targetTypeColors[rule.target_type] || targetTypeColors.DEFAULT
                      }`}
                    >
                      {rule.target_type.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {rule.target_value}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                    {rule.markup_type === "PERCENTAGE" ? `${rule.markup_value}%` : `$${rule.markup_value}`}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {rule.priority}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        rule.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {rule.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {rules.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              No markup rules configured yet
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">How Markup Rules Work</h3>
        <p className="text-sm text-blue-800">
          Markup rules are applied to calculate customer pricing from internal costs.
          Rules with higher priority take precedence when multiple rules match.
          For example, a rule for "ENGINE" parts with priority 10 will override a
          "DEFAULT" rule with priority 5.
        </p>
      </div>
    </div>
  );
}
