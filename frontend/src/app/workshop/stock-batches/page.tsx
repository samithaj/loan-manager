"use client";
import { useState } from "react";
import StockReceiveForm from "@/components/workshop/stock/StockReceiveForm";

export default function StockBatchesPage() {
  const [showReceiveForm, setShowReceiveForm] = useState(false);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Stock Batches</h1>
          <p className="text-gray-600 mt-1">
            Manage stock batches, receive new inventory, and track movements
          </p>
        </div>
        <button
          onClick={() => setShowReceiveForm(!showReceiveForm)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          {showReceiveForm ? "Hide Form" : "Receive Stock"}
        </button>
      </div>

      {showReceiveForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Receive New Stock</h2>
          <StockReceiveForm
            onSuccess={() => {
              setShowReceiveForm(false);
              // Refresh the batches list
            }}
            onCancel={() => setShowReceiveForm(false)}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Stock Batches</h2>
        <div className="text-center text-gray-500 py-12">
          Stock batches list will be displayed here
        </div>
      </div>
    </div>
  );
}
