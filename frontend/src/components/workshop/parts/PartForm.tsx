"use client";
import { useState, useEffect } from "react";
import CategoryBadge, { PartCategory } from "../common/CategoryBadge";

interface PartFormData {
  part_code: string;
  name: string;
  description: string;
  category: PartCategory;
  brand: string;
  unit: string;
  is_universal: boolean;
  minimum_stock_level: number;
  reorder_point: number;
  is_active: boolean;
}

interface PartFormProps {
  mode: "create" | "edit";
  partId?: number;
  initialData?: Partial<PartFormData>;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const CATEGORIES: PartCategory[] = [
  "ENGINE",
  "BRAKE",
  "TYRE",
  "ELECTRICAL",
  "SUSPENSION",
  "TRANSMISSION",
  "EXHAUST",
  "BODY",
  "ACCESSORIES",
  "FLUIDS",
  "CONSUMABLES",
  "OTHER",
];

const UNITS = ["pcs", "set", "litre", "kg", "metre", "pair", "roll", "box", "bottle"];

export default function PartForm({
  mode,
  partId,
  initialData,
  onSuccess,
  onCancel,
}: PartFormProps) {
  const [formData, setFormData] = useState<PartFormData>({
    part_code: "",
    name: "",
    description: "",
    category: "OTHER",
    brand: "",
    unit: "pcs",
    is_universal: true,
    minimum_stock_level: 0,
    reorder_point: 0,
    is_active: true,
    ...initialData,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const url =
        mode === "create"
          ? `${base}/v1/workshop/parts`
          : `${base}/v1/workshop/parts/${partId}`;
      const method = mode === "create" ? "POST" : "PUT";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        onSuccess?.();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to save part");
      }
    } catch (err) {
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Part Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Part Code <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={formData.part_code}
            onChange={(e) =>
              setFormData({ ...formData, part_code: e.target.value.toUpperCase() })
            }
            placeholder="e.g., BRK-PAD-001"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">Unique identifier for this part</p>
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Part Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Front Brake Pad - Yaris"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Detailed description of the part..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category <span className="text-red-500">*</span>
          </label>
          <select
            required
            value={formData.category}
            onChange={(e) =>
              setFormData({ ...formData, category: e.target.value as PartCategory })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          <div className="mt-2">
            <CategoryBadge category={formData.category} size="sm" />
          </div>
        </div>

        {/* Brand */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
          <input
            type="text"
            value={formData.brand}
            onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
            placeholder="e.g., Bosch, Brembo"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Unit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Unit <span className="text-red-500">*</span>
          </label>
          <select
            required
            value={formData.unit}
            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {UNITS.map((unit) => (
              <option key={unit} value={unit}>
                {unit}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Minimum Stock Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Stock Level
          </label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formData.minimum_stock_level}
            onChange={(e) =>
              setFormData({ ...formData, minimum_stock_level: parseFloat(e.target.value) || 0 })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Alert when stock falls below this</p>
        </div>

        {/* Reorder Point */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reorder Point
          </label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={formData.reorder_point}
            onChange={(e) =>
              setFormData({ ...formData, reorder_point: parseFloat(e.target.value) || 0 })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Trigger purchase order at this level</p>
        </div>

        {/* Is Universal */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Part Type
          </label>
          <div className="flex items-center gap-4 mt-2">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={formData.is_universal}
                onChange={() => setFormData({ ...formData, is_universal: true })}
                className="w-4 h-4 text-blue-600"
              />
              <span className="text-sm text-gray-700">Universal</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={!formData.is_universal}
                onChange={() => setFormData({ ...formData, is_universal: false })}
                className="w-4 h-4 text-blue-600"
              />
              <span className="text-sm text-gray-700">Bike Specific</span>
            </label>
          </div>
        </div>
      </div>

      {/* Active Status */}
      <div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm font-medium text-gray-700">Active (visible in searches)</span>
        </label>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-6 border-t">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
        >
          {loading ? "Saving..." : mode === "create" ? "Create Part" : "Update Part"}
        </button>
      </div>
    </form>
  );
}
