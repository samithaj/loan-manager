"use client";
import { useState, useRef } from "react";
import { useReactToPrint } from "react-to-print";
import ReceiptComponent from "./ReceiptComponent";

type Transaction = {
  id: string;
  loanId: string;
  type: string;
  amount: number;
  date: string;
  receiptNumber: string;
  postedBy?: string | null;
};

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
  createdOn: string;
};

interface PaymentFormProps {
  loan: Loan;
  onTransactionComplete: (transaction: Transaction) => void;
  onClose: () => void;
}

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function PaymentForm({ loan, onTransactionComplete, onClose }: PaymentFormProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [command, setCommand] = useState("repayment");
  const [amount, setAmount] = useState("");
  const [transactionDate, setTransactionDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTransaction, setLastTransaction] = useState<Transaction | null>(null);
  const [showReceipt, setShowReceipt] = useState(false);
  
  const receiptRef = useRef<HTMLDivElement>(null);
  
  const handlePrint = useReactToPrint({
    content: () => receiptRef.current,
    documentTitle: `Receipt-${lastTransaction?.receiptNumber}`,
  });

  async function loadTemplate() {
    try {
      const res = await fetch(
        `${base}/v1/loans/${loan.id}/transactions/template?command=${command}`,
        { headers: authHeaders() }
      );
      if (res.ok) {
        const template = await res.json();
        setAmount(template.suggestedAmount.toString());
      }
    } catch {
      // Ignore template loading errors
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const url = new URL(`${base}/v1/loans/${loan.id}/transactions`);
      url.searchParams.set("command", command);
      url.searchParams.set("amount", amount);
      if (transactionDate) {
        url.searchParams.set("transactionDate", transactionDate);
      }

      const res = await fetch(url.toString(), {
        method: "POST",
        headers: {
          "Idempotency-Key": `${command}-${loan.id}-${Date.now()}`,
          ...authHeaders()
        }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      const result = await res.json();
      const transaction = result.transaction;
      
      setLastTransaction(transaction);
      setShowReceipt(true);
      onTransactionComplete(transaction);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const commandLabels: Record<string, string> = {
    repayment: "Regular Repayment",
    prepay: "Prepayment",
    foreclosure: "Foreclosure",
    writeoff: "Write-off",
    waiveInterest: "Waive Interest",
    recovery: "Recovery"
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">Record Payment</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        </div>

        {!showReceipt ? (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Type *
              </label>
              <select
                value={command}
                onChange={(e) => {
                  setCommand(e.target.value);
                  loadTemplate();
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(commandLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Date *
              </label>
              <input
                type="date"
                value={transactionDate}
                onChange={(e) => setTransactionDate(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="flex gap-2 justify-end pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? "Processing..." : "Record Payment"}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
              Payment recorded successfully! Receipt number: {lastTransaction?.receiptNumber}
            </div>
            
            <div className="flex gap-2 justify-end">
              <button
                onClick={handlePrint}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Print Receipt
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Close
              </button>
            </div>

            {/* Hidden receipt component for printing */}
            <div style={{ display: "none" }}>
              <ReceiptComponent
                ref={receiptRef}
                loan={loan}
                transaction={lastTransaction!}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}