"use client";
import { useEffect, useState, useRef } from "react";
import { useReactToPrint } from "react-to-print";
import ReceiptComponent from "./ReceiptComponent";

type Charge = {
  id: string;
  loanId: string;
  name: string;
  amount: number;
  dueDate?: string | null;
  status: string;
};

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

interface ChargesManagerProps {
  loan: Loan;
}

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function ChargesManager({ loan }: ChargesManagerProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [charges, setCharges] = useState<Charge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCharge, setEditingCharge] = useState<Charge | null>(null);
  const [form, setForm] = useState({
    name: "",
    amount: "",
    dueDate: ""
  });
  const [paymentForm, setPaymentForm] = useState({
    chargeId: "",
    amount: "",
    paymentDate: new Date().toISOString().split('T')[0]
  });
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [lastTransaction, setLastTransaction] = useState<Transaction | null>(null);
  const [showReceipt, setShowReceipt] = useState(false);
  
  const receiptRef = useRef<HTMLDivElement>(null);
  
  const handlePrint = useReactToPrint({
    content: () => receiptRef.current,
    documentTitle: `Receipt-${lastTransaction?.receiptNumber}`,
  });

  async function loadCharges() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loans/${loan.id}/charges`, {
        cache: "no-store",
        headers: authHeaders()
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Charge[];
      setCharges(data);
    } catch {
      setError("Failed to load charges");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCharges();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loan.id]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const payload = {
      id: editingCharge?.id || `CHG${Date.now()}`,
      name: form.name,
      amount: parseFloat(form.amount),
      dueDate: form.dueDate || undefined
    };

    try {
      const method = editingCharge ? "PUT" : "POST";
      const url = editingCharge 
        ? `${base}/v1/loans/${loan.id}/charges/${editingCharge.id}`
        : `${base}/v1/loans/${loan.id}/charges`;
      
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      setForm({ name: "", amount: "", dueDate: "" });
      setEditingCharge(null);
      setShowForm(false);
      await loadCharges();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function onDelete(chargeId: string) {
    if (!confirm("Are you sure you want to delete this charge?")) return;
    
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loans/${loan.id}/charges/${chargeId}`, {
        method: "DELETE",
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      await loadCharges();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function onPayCharge(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      const url = new URL(`${base}/v1/loans/${loan.id}/charges/${paymentForm.chargeId}/pay`);
      if (paymentForm.amount) {
        url.searchParams.set("amount", paymentForm.amount);
      }
      if (paymentForm.paymentDate) {
        url.searchParams.set("paymentDate", paymentForm.paymentDate);
      }

      const res = await fetch(url.toString(), {
        method: "POST",
        headers: {
          "Idempotency-Key": `pay-${paymentForm.chargeId}-${Date.now()}`,
          ...authHeaders()
        }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      const result = await res.json();
      setLastTransaction(result.transaction);
      setShowReceipt(true);
      setShowPaymentForm(false);
      setPaymentForm({ chargeId: "", amount: "", paymentDate: new Date().toISOString().split('T')[0] });
      await loadCharges();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function startEdit(charge: Charge) {
    setEditingCharge(charge);
    setForm({
      name: charge.name,
      amount: charge.amount.toString(),
      dueDate: charge.dueDate || ""
    });
    setShowForm(true);
  }

  function startPayment(charge: Charge) {
    setPaymentForm({
      chargeId: charge.id,
      amount: charge.amount.toString(),
      paymentDate: new Date().toISOString().split('T')[0]
    });
    setShowPaymentForm(true);
  }

  const statusBadgeColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-yellow-100 text-yellow-800";
      case "PAID": return "bg-green-100 text-green-800";
      case "WAIVED": return "bg-blue-100 text-blue-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Charges</h3>
        <button
          onClick={() => {
            setEditingCharge(null);
            setForm({ name: "", amount: "", dueDate: "" });
            setShowForm(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Charge
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-4">Loading charges...</div>
      ) : charges.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No charges found</div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Due Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {charges.map((charge) => (
                <tr key={charge.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {charge.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${charge.amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {charge.dueDate ? new Date(charge.dueDate).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusBadgeColor(charge.status)}`}>
                      {charge.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex gap-2">
                      {charge.status === "PENDING" && (
                        <>
                          <button
                            onClick={() => startEdit(charge)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => startPayment(charge)}
                            className="text-green-600 hover:text-green-800"
                          >
                            Pay
                          </button>
                          <button
                            onClick={() => onDelete(charge.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">
              {editingCharge ? "Edit Charge" : "Add Charge"}
            </h3>
            
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Charge Name *
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  value={form.dueDate}
                  onChange={(e) => setForm({ ...form, dueDate: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingCharge(null);
                    setForm({ name: "", amount: "", dueDate: "" });
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingCharge ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Payment Form Modal */}
      {showPaymentForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">Pay Charge</h3>
            
            <form onSubmit={onPayCharge} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Amount *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Date *
                </label>
                <input
                  type="date"
                  value={paymentForm.paymentDate}
                  onChange={(e) => setPaymentForm({ ...paymentForm, paymentDate: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowPaymentForm(false);
                    setPaymentForm({ chargeId: "", amount: "", paymentDate: new Date().toISOString().split('T')[0] });
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Record Payment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Receipt Modal */}
      {showReceipt && lastTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="text-center mb-4">
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
                Payment recorded successfully! Receipt: {lastTransaction.receiptNumber}
              </div>
              
              <div className="flex gap-2 justify-center">
                <button
                  onClick={handlePrint}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Print Receipt
                </button>
                <button
                  onClick={() => {
                    setShowReceipt(false);
                    setLastTransaction(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Close
                </button>
              </div>
            </div>

            {/* Hidden receipt component for printing */}
            <div style={{ display: "none" }}>
              <ReceiptComponent
                ref={receiptRef}
                loan={loan}
                transaction={lastTransaction}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}