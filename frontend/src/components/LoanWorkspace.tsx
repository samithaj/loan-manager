"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import PaymentForm from "./PaymentForm";
import ChargesManager from "./ChargesManager";
import CollateralManager from "./CollateralManager";
import DocumentManager from "./DocumentManager";

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

type Transaction = {
  id: string;
  loanId: string;
  type: string;
  amount: number;
  date: string;
  receiptNumber: string;
  postedBy?: string | null;
};

type Client = { id: string; displayName: string };
type LoanProduct = { id: string; name: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

interface LoanWorkspaceProps {
  loanId: string;
}

export default function LoanWorkspace({ loanId }: LoanWorkspaceProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [loan, setLoan] = useState<Loan | null>(null);
  const [client, setClient] = useState<Client | null>(null);
  const [product, setProduct] = useState<LoanProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showActionDrawer, setShowActionDrawer] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [disbursementDate, setDisbursementDate] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  async function loadLoan() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base}/v1/loans/${loanId}`, { 
        cache: "no-store", 
        headers: authHeaders() 
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const loanData = (await res.json()) as Loan;
      setLoan(loanData);

      // Load related client, product data, and transactions
      const [clientRes, productRes, transactionsRes] = await Promise.all([
        fetch(`${base}/v1/clients/${loanData.clientId}`, { headers: authHeaders() }),
        fetch(`${base}/v1/loan-products`, { headers: authHeaders() }),
        fetch(`${base}/v1/loans/${loanId}/transactions`, { headers: authHeaders() })
      ]);

      if (clientRes.ok) {
        const clientData = await clientRes.json();
        setClient(clientData);
      }

      if (productRes.ok) {
        const productsData = await productRes.json();
        const productData = productsData.find((p: LoanProduct) => p.id === loanData.productId);
        setProduct(productData || null);
      }

      if (transactionsRes.ok) {
        const transactionsData = await transactionsRes.json();
        setTransactions(transactionsData);
      }
    } catch {
      setError("Failed to load loan");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLoan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loanId]);

  async function executeCommand(command: string) {
    if (!loan) return;
    
    setActionLoading(command);
    setError(null);
    
    try {
      const url = new URL(`${base}/v1/loans/${loanId}`);
      url.searchParams.set("command", command);
      if (command === "disburse" && disbursementDate) {
        url.searchParams.set("disbursementDate", disbursementDate);
      }

      const res = await fetch(url.toString(), {
        method: "POST",
        headers: {
          "Idempotency-Key": `${command}-${loanId}-${Date.now()}`,
          ...authHeaders()
        }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      const result = await res.json();
      setLoan(result.loan);
      setShowActionDrawer(false);
      setSelectedAction(null);
      setDisbursementDate("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  }

  function openActionDrawer(action: string) {
    setSelectedAction(action);
    setShowActionDrawer(true);
    if (action === "disburse") {
      setDisbursementDate(new Date().toISOString().split('T')[0]);
    }
  }

  const statusBadgeColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-yellow-100 text-yellow-800";
      case "APPROVED": return "bg-blue-100 text-blue-800";
      case "DISBURSED": return "bg-green-100 text-green-800";
      case "CLOSED": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getAvailableActions = () => {
    if (!loan) return [];
    switch (loan.status) {
      case "PENDING": return ["approve"];
      case "APPROVED": return ["disburse", "close"];
      case "DISBURSED": return ["close"];
      default: return [];
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading loan...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!loan) {
    return (
      <div className="text-center py-8">
        <div className="text-lg text-gray-600">Loan not found</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-4">
              <Link href="/loans" className="text-blue-600 hover:text-blue-800">
                ← Back to Loans
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">Loan {loan.id}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusBadgeColor(loan.status)}`}>
                {loan.status}
              </span>
            </div>
            <div className="mt-2 text-gray-600">
              {client?.displayName} • {product?.name} • ${loan.principal.toLocaleString()}
            </div>
          </div>
          
          <div className="flex gap-2">
            {getAvailableActions().map((action) => (
              <button
                key={action}
                onClick={() => openActionDrawer(action)}
                disabled={actionLoading === action}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {actionLoading === action ? "Processing..." : action.charAt(0).toUpperCase() + action.slice(1)}
              </button>
            ))}
            {loan.status === "DISBURSED" && (
              <button
                onClick={() => setShowPaymentForm(true)}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Record Payment
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">Loan Timeline</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <div className="font-medium">Loan Created</div>
              <div className="text-sm text-gray-600">{new Date(loan.createdOn).toLocaleString()}</div>
            </div>
          </div>
          
          {loan.status !== "PENDING" && (
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <div>
                <div className="font-medium">Loan Approved</div>
                <div className="text-sm text-gray-600">Status changed to APPROVED</div>
              </div>
            </div>
          )}
          
          {loan.disbursedOn && (
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div>
                <div className="font-medium">Loan Disbursed</div>
                <div className="text-sm text-gray-600">{new Date(loan.disbursedOn).toLocaleDateString()}</div>
              </div>
            </div>
          )}
          
          {loan.status === "CLOSED" && (
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
              <div>
                <div className="font-medium">Loan Closed</div>
                <div className="text-sm text-gray-600">Status changed to CLOSED</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Loan Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-medium mb-4">Loan Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Basic Information</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-gray-600">Client:</dt>
                <dd className="font-medium">{client?.displayName || loan.clientId}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Product:</dt>
                <dd className="font-medium">{product?.name || loan.productId}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Principal:</dt>
                <dd className="font-medium">${loan.principal.toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Interest Rate:</dt>
                <dd className="font-medium">{loan.interestRate}%</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Term:</dt>
                <dd className="font-medium">{loan.termMonths} months</dd>
              </div>
            </dl>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Status Information</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-gray-600">Status:</dt>
                <dd>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadgeColor(loan.status)}`}>
                    {loan.status}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Created:</dt>
                <dd className="font-medium">{new Date(loan.createdOn).toLocaleDateString()}</dd>
              </div>
              {loan.disbursedOn && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Disbursed:</dt>
                  <dd className="font-medium">{new Date(loan.disbursedOn).toLocaleDateString()}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>

      {/* Transaction History */}
      {transactions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-medium mb-4">Transaction History</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Receipt #
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(tx.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                        {tx.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${tx.amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tx.receiptNumber}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Charges Management */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <ChargesManager loan={loan} />
      </div>

      {/* Collateral Management */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <CollateralManager loan={loan} />
      </div>

      {/* Document Management */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <DocumentManager ownerType="LOAN" ownerId={loan.id} title="Loan Documents" />
      </div>

      {/* Payment Form Modal */}
      {showPaymentForm && (
        <PaymentForm
          loan={loan}
          onTransactionComplete={(transaction) => {
            setTransactions([transaction, ...transactions]);
            setShowPaymentForm(false);
          }}
          onClose={() => setShowPaymentForm(false)}
        />
      )}

      {/* Action Drawer */}
      {showActionDrawer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">
              {selectedAction?.charAt(0).toUpperCase()}{selectedAction?.slice(1)} Loan
            </h3>
            
            {selectedAction === "approve" && (
              <div>
                <p className="text-gray-600 mb-4">
                  Are you sure you want to approve this loan? This action cannot be undone.
                </p>
              </div>
            )}
            
            {selectedAction === "disburse" && (
              <div>
                <p className="text-gray-600 mb-4">
                  Disburse the loan amount to the client. This will create a disbursement transaction.
                </p>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Disbursement Date
                  </label>
                  <input
                    type="date"
                    value={disbursementDate}
                    onChange={(e) => setDisbursementDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
            
            {selectedAction === "close" && (
              <div>
                <p className="text-gray-600 mb-4">
                  Are you sure you want to close this loan? This action cannot be undone.
                </p>
              </div>
            )}
            
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowActionDrawer(false);
                  setSelectedAction(null);
                  setDisbursementDate("");
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={() => selectedAction && executeCommand(selectedAction)}
                disabled={actionLoading !== null}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {actionLoading ? "Processing..." : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}