"use client";
import { useState } from "react";
import PartSearch from "../common/PartSearch";
import CurrencyInput from "../common/CurrencyInput";

interface StockReceiveFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function StockReceiveForm({ onSuccess, onCancel }: StockReceiveFormProps) {
  const [formData, setFormData] = useState({
    partId: null as number | null,
    partName: "",
    supplierId: null as number | null,
    branchId: null as number | null,
    purchaseDate: new Date().toISOString().split("T")[0],
    purchasePricePerUnit: 0,
    quantityReceived: 0,
    expiryDate: "",
    invoiceNo: "",
    grnNo: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.partId) {
      setError("Please select a part");
      return;
    }
    if (formData.quantityReceived <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${base}/v1/workshop/parts/${formData.partId}/stock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          supplier_id: formData.supplierId,
          branch_id: formData.branchId,
          purchase_date: formData.purchaseDate,
          purchase_price_per_unit: formData.purchasePricePerUnit,
          quantity_received: formData.quantityReceived,
          expiry_date: formData.expiryDate || null,
          invoice_no: formData.invoiceNo,
          grn_no: formData.grnNo,
        }),
      });

      if (res.ok) {
        onSuccess?.();
        // Reset form
        setFormData({
          partId: null,
          partName: "",
          supplierId: null,
          branchId: null,
          purchaseDate: new Date().toISOString().split("T")[0],
          purchasePricePerUnit: 0,
          quantityReceived: 0,
          expiryDate: "",
          invoiceNo: "",
          grnNo: "",
        });
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to receive stock");
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

      {/* Part Selection */}
      <PartSearch
        onSelect={(part) => {
          setFormData({
            ...formData,
            partId: part.id,
            partName: `${part.part_code} - ${part.name}`,
          });
        }}
        label="Select Part"
        placeholder="Search by part code or name..."
        required
      />

      {formData.partName && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
          Selected: <strong>{formData.partName}</strong>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Purchase Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Purchase Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            required
            value={formData.purchaseDate}
            onChange={(e) => setFormData({ ...formData, purchaseDate: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Branch */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Branch <span className="text-red-500">*</span>
          </label>
          <select
            required
            value={formData.branchId || ""}
            onChange={(e) =>
              setFormData({ ...formData, branchId: e.target.value ? Number(e.target.value) : null })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select branch...</option>
            <option value="1">Main Branch</option>
            <option value="2">Workshop Branch</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Unit Price */}
        <CurrencyInput
          label="Purchase Price Per Unit"
          value={formData.purchasePricePerUnit}
          onChange={(value) => setFormData({ ...formData, purchasePricePerUnit: value })}
          required
          min={0}
        />

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity Received <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            required
            min="0.01"
            step="0.01"
            value={formData.quantityReceived || ""}
            onChange={(e) =>
              setFormData({ ...formData, quantityReceived: parseFloat(e.target.value) || 0 })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Total Cost Preview */}
      {formData.purchasePricePerUnit > 0 && formData.quantityReceived > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-800">
            <strong>Total Cost:</strong> $
            {(formData.purchasePricePerUnit * formData.quantityReceived).toFixed(2)}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Invoice Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Invoice Number</label>
          <input
            type="text"
            value={formData.invoiceNo}
            onChange={(e) => setFormData({ ...formData, invoiceNo: e.target.value })}
            placeholder="INV-12345"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* GRN Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">GRN Number</label>
          <input
            type="text"
            value={formData.grnNo}
            onChange={(e) => setFormData({ ...formData, grnNo: e.target.value })}
            placeholder="GRN-12345"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Expiry Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Expiry Date (if applicable)
          </label>
          <input
            type="date"
            value={formData.expiryDate}
            onChange={(e) => setFormData({ ...formData, expiryDate: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
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
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
        >
          {loading ? "Receiving..." : "Receive Stock"}
        </button>
      </div>
    </form>
  );
}
