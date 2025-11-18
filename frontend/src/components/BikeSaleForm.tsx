"use client";

import { useState } from "react";

interface BikeSaleFormProps {
  bikeId: string;
  currentPrice?: number;
  totalCost?: number;
  onSubmit: (saleData: SaleFormData) => Promise<void>;
  onCancel: () => void;
}

export interface SaleFormData {
  bicycle_id: string;
  selling_price: number;
  sale_date: string;
  selling_branch_id: string;
  sold_by: string;
  customer_name: string;
  customer_contact: string;
  customer_address?: string;
  customer_nic?: string;
  payment_method: "CASH" | "FINANCE" | "TRADE_IN" | "BANK_TRANSFER" | "MIXED";
  finance_institution?: string;
  trade_in_bike_model?: string;
  trade_in_value?: number;
  down_payment?: number;
  notes?: string;
}

export default function BikeSaleForm({
  bikeId,
  currentPrice,
  totalCost,
  onSubmit,
  onCancel
}: BikeSaleFormProps) {
  const [formData, setFormData] = useState<Partial<SaleFormData>>({
    bicycle_id: bikeId,
    selling_price: currentPrice || 0,
    sale_date: new Date().toISOString().split("T")[0],
    payment_method: "CASH"
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const calculateProfit = () => {
    if (!totalCost || !formData.selling_price) return null;
    return formData.selling_price - totalCost;
  };

  const profit = calculateProfit();
  const profitColor = profit
    ? profit > 0
      ? "text-green-600"
      : profit < 0
      ? "text-red-600"
      : "text-gray-600"
    : "text-gray-400";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.selling_price || formData.selling_price <= 0) {
      setError("Please enter a valid selling price");
      return;
    }
    if (!formData.selling_branch_id) {
      setError("Please select a selling branch");
      return;
    }
    if (!formData.sold_by) {
      setError("Please enter seller name");
      return;
    }
    if (!formData.customer_name) {
      setError("Please enter customer name");
      return;
    }
    if (!formData.customer_contact) {
      setError("Please enter customer contact");
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(formData as SaleFormData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record sale");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Record Bike Sale</h2>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* P/L Preview */}
      {totalCost && profit !== null && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-gray-500 mb-1">Total Cost</div>
              <div className="font-semibold text-gray-900">{formatCurrency(totalCost)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Selling Price</div>
              <div className="font-semibold text-gray-900">
                {formatCurrency(formData.selling_price || 0)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Profit/Loss</div>
              <div className={`font-bold ${profitColor}`}>{formatCurrency(profit)}</div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {/* Sale Details */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Selling Price <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.selling_price || ""}
              onChange={(e) =>
                setFormData({ ...formData, selling_price: parseFloat(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sale Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={formData.sale_date || ""}
              onChange={(e) => setFormData({ ...formData, sale_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Selling Branch <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.selling_branch_id || ""}
              onChange={(e) => setFormData({ ...formData, selling_branch_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., WW, HP, BRC"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sold By <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.sold_by || ""}
              onChange={(e) => setFormData({ ...formData, sold_by: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Seller name"
              required
            />
          </div>
        </div>

        {/* Customer Details */}
        <div className="pt-4 border-t">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Details</h3>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.customer_name || ""}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  value={formData.customer_contact || ""}
                  onChange={(e) => setFormData({ ...formData, customer_contact: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="07xxxxxxxx"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  NIC Number
                </label>
                <input
                  type="text"
                  value={formData.customer_nic || ""}
                  onChange={(e) => setFormData({ ...formData, customer_nic: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="NIC or Passport"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={formData.customer_address || ""}
                  onChange={(e) => setFormData({ ...formData, customer_address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Customer address"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Payment Details */}
        <div className="pt-4 border-t">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Details</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payment Method <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.payment_method || "CASH"}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    payment_method: e.target.value as SaleFormData["payment_method"]
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="CASH">Cash</option>
                <option value="FINANCE">Finance</option>
                <option value="TRADE_IN">Trade-in</option>
                <option value="BANK_TRANSFER">Bank Transfer</option>
                <option value="MIXED">Mixed</option>
              </select>
            </div>

            {formData.payment_method === "FINANCE" && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Finance Institution
                  </label>
                  <input
                    type="text"
                    value={formData.finance_institution || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, finance_institution: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Bank of Ceylon"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Down Payment
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.down_payment || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, down_payment: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {formData.payment_method === "TRADE_IN" && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trade-in Bike Model
                  </label>
                  <input
                    type="text"
                    value={formData.trade_in_bike_model || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, trade_in_bike_model: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Old bike model"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Trade-in Value
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.trade_in_value || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, trade_in_value: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            value={formData.notes || ""}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Additional notes about the sale"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="mt-6 flex gap-3 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Recording Sale..." : "Record Sale"}
        </button>
      </div>
    </form>
  );
}
