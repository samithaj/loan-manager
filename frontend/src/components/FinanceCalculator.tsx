"use client";

import { useState } from "react";
import Link from "next/link";

interface FinanceCalculatorProps {
  bicycleId: string;
  cashPrice: number;
  hirePurchasePrice: number;
}

export default function FinanceCalculator({
  bicycleId,
  cashPrice,
  hirePurchasePrice,
}: FinanceCalculatorProps) {
  const [downPayment, setDownPayment] = useState(hirePurchasePrice * 0.2); // Default 20%
  const [tenure, setTenure] = useState(36); // Default 36 months

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const financedAmount = hirePurchasePrice - downPayment;
  const monthlyPayment = financedAmount / tenure;
  const totalPayable = downPayment + (monthlyPayment * tenure);
  const savingsVsCash = totalPayable - cashPrice;

  const minDownPayment = hirePurchasePrice * 0.1; // 10% minimum
  const maxDownPayment = hirePurchasePrice * 0.9; // 90% maximum

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 sticky top-24">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Finance Calculator</h3>

      {/* Down Payment */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-gray-700">Down Payment</label>
          <span className="text-lg font-bold text-blue-600">
            {formatCurrency(downPayment)}
          </span>
        </div>
        <input
          type="range"
          min={minDownPayment}
          max={maxDownPayment}
          step={100000}
          value={downPayment}
          onChange={(e) => setDownPayment(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{Math.round((downPayment / hirePurchasePrice) * 100)}%</span>
          <span>{formatCurrency(minDownPayment)} - {formatCurrency(maxDownPayment)}</span>
        </div>
      </div>

      {/* Tenure */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Payment Period
        </label>
        <div className="grid grid-cols-4 gap-2">
          {[12, 24, 36, 48].map((months) => (
            <button
              key={months}
              onClick={() => setTenure(months)}
              className={`px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${
                tenure === months
                  ? "bg-blue-600 text-white border-blue-600"
                  : "border-gray-300 text-gray-700 hover:border-blue-600 hover:text-blue-600"
              }`}
            >
              {months}m
            </button>
          ))}
        </div>
      </div>

      {/* Monthly Payment */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <div className="text-sm text-gray-600 mb-1">Monthly Payment</div>
        <div className="text-3xl font-bold text-blue-600">
          {formatCurrency(monthlyPayment)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          for {tenure} months
        </div>
      </div>

      {/* Payment Breakdown */}
      <div className="border-t pt-4 mb-6 space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Cash Price</span>
          <span className="font-medium text-gray-900">{formatCurrency(cashPrice)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Hire Purchase Price</span>
          <span className="font-medium text-gray-900">{formatCurrency(hirePurchasePrice)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Down Payment</span>
          <span className="font-medium text-gray-900">{formatCurrency(downPayment)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Financed Amount</span>
          <span className="font-medium text-gray-900">{formatCurrency(financedAmount)}</span>
        </div>
        <div className="flex justify-between pt-2 border-t font-semibold">
          <span className="text-gray-900">Total Payable</span>
          <span className="text-gray-900">{formatCurrency(totalPayable)}</span>
        </div>
        {savingsVsCash > 0 && (
          <div className="text-xs text-gray-500 text-center pt-2">
            ({formatCurrency(savingsVsCash)} more than cash price)
          </div>
        )}
      </div>

      {/* Apply Button */}
      <Link
        href={`/bicycles/apply?bicycle_id=${bicycleId}&down_payment=${downPayment}&tenure=${tenure}`}
        className="block w-full bg-blue-600 text-white text-center py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
      >
        Apply for This Bicycle
      </Link>

      <p className="text-xs text-gray-500 text-center mt-3">
        * This is an estimate. Final terms subject to approval.
      </p>
    </div>
  );
}
