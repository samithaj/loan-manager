"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { ApplicationResponse, Bicycle } from "@/types/bicycle";

export default function ApplicationDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [bicycle, setBicycle] = useState<Bicycle | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  useEffect(() => {
    async function loadApplication() {
      try {
        const res = await fetch(`${baseUrl}/v1/bicycle-applications/${params.id}`, {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch application");
        }

        const data: ApplicationResponse = await res.json();
        setApplication(data);

        // Load bicycle details if we have an ID
        if (data.bicycle_id) {
          try {
            const bicycleRes = await fetch(`${baseUrl}/v1/bicycles/${data.bicycle_id}`, {
              credentials: "include",
            });
            if (bicycleRes.ok) {
              const bicycleData = await bicycleRes.json();
              setBicycle(bicycleData);
            }
          } catch (err) {
            console.error("Failed to load bicycle:", err);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load application");
      } finally {
        setLoading(false);
      }
    }

    loadApplication();
  }, [baseUrl, params.id]);

  const handleApprove = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const res = await fetch(`${baseUrl}/v1/bicycle-applications/${params.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ notes }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || "Failed to approve application");
      }

      const result = await res.json();
      alert(`Application approved! Loan ID: ${result.loan_id}`);
      router.push("/applications");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve application");
    } finally {
      setActionLoading(false);
      setShowApproveDialog(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const res = await fetch(`${baseUrl}/v1/bicycle-applications/${params.id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ notes: notes || "Application rejected" }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.message || "Failed to reject application");
      }

      alert("Application rejected successfully");
      router.push("/applications");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject application");
    } finally {
      setActionLoading(false);
      setShowRejectDialog(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
      </div>
    );
  }

  if (error && !application) {
    return (
      <div className="min-h-screen max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-600">{error}</p>
          <Link href="/applications" className="text-blue-600 hover:text-blue-700 underline mt-4 inline-block">
            Back to Applications
          </Link>
        </div>
      </div>
    );
  }

  if (!application) {
    return null;
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      PENDING: "bg-yellow-100 text-yellow-800",
      UNDER_REVIEW: "bg-blue-100 text-blue-800",
      APPROVED: "bg-green-100 text-green-800",
      REJECTED: "bg-red-100 text-red-800",
      CONVERTED_TO_LOAN: "bg-purple-100 text-purple-800",
    };
    return styles[status] || "bg-gray-100 text-gray-800";
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("id-ID", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const canApproveOrReject = application.status === "PENDING" || application.status === "UNDER_REVIEW";

  return (
    <div className="min-h-screen max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href="/applications" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
          ← Back to Applications
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Application Details</h1>
            <p className="text-gray-600 font-mono">{application.id}</p>
          </div>
          <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusBadge(application.status)}`}>
            {application.status.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Customer Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">Full Name</div>
                <div className="font-medium text-gray-900">{application.full_name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Phone</div>
                <div className="font-medium text-gray-900">{application.phone}</div>
              </div>
              {application.email && (
                <div>
                  <div className="text-sm text-gray-600">Email</div>
                  <div className="font-medium text-gray-900">{application.email}</div>
                </div>
              )}
              {application.nip_number && (
                <div>
                  <div className="text-sm text-gray-600">NIP Number</div>
                  <div className="font-medium text-gray-900">{application.nip_number}</div>
                </div>
              )}
            </div>
          </div>

          {/* Address */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Address</h2>
            <div className="space-y-2">
              <p className="text-gray-900">{application.address_line1}</p>
              {application.address_line2 && <p className="text-gray-900">{application.address_line2}</p>}
              <p className="text-gray-900">{application.city}</p>
            </div>
          </div>

          {/* Employment */}
          {(application.employer_name || application.monthly_income) && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Employment</h2>
              <div className="grid grid-cols-2 gap-4">
                {application.employer_name && (
                  <div>
                    <div className="text-sm text-gray-600">Employer</div>
                    <div className="font-medium text-gray-900">{application.employer_name}</div>
                  </div>
                )}
                {application.monthly_income && (
                  <div>
                    <div className="text-sm text-gray-600">Monthly Income</div>
                    <div className="font-medium text-gray-900">{formatCurrency(application.monthly_income)}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Bicycle & Finance */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Bicycle & Finance Details</h2>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-600">Bicycle ID</div>
                <div className="font-medium text-gray-900">{application.bicycle_id}</div>
              </div>
              {bicycle && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="font-medium text-gray-900 mb-2">{bicycle.title}</div>
                  <div className="text-sm text-gray-600">
                    {bicycle.brand} {bicycle.model} ({bicycle.year}) - {bicycle.condition}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Branch</div>
                  <div className="font-medium text-gray-900">{application.branch_id}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Tenure</div>
                  <div className="font-medium text-gray-900">{application.tenure_months} months</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Down Payment</div>
                  <div className="font-medium text-gray-900">{formatCurrency(application.down_payment)}</div>
                </div>
                {bicycle && (
                  <div>
                    <div className="text-sm text-gray-600">Monthly Payment (Est.)</div>
                    <div className="font-medium text-blue-600">
                      {formatCurrency((bicycle.hire_purchase_price - application.down_payment) / application.tenure_months)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Review History */}
          {application.notes && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Review Notes</h2>
              <p className="text-gray-700 whitespace-pre-line">{application.notes}</p>
              {application.reviewed_at && (
                <p className="text-sm text-gray-500 mt-2">
                  Reviewed on {formatDate(application.reviewed_at)}
                  {application.reviewed_by && ` by ${application.reviewed_by}`}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Timeline */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm font-medium text-gray-900">Submitted</div>
                <div className="text-xs text-gray-500">{formatDate(application.submitted_at)}</div>
              </div>
              {application.reviewed_at && (
                <div>
                  <div className="text-sm font-medium text-gray-900">Reviewed</div>
                  <div className="text-xs text-gray-500">{formatDate(application.reviewed_at)}</div>
                </div>
              )}
              {application.loan_id && (
                <div>
                  <div className="text-sm font-medium text-gray-900">Loan Created</div>
                  <div className="text-xs text-gray-500 font-mono">{application.loan_id}</div>
                </div>
              )}
            </div>
          </div>

          {/* Linked Loan */}
          {application.loan_id && application.status === "CONVERTED_TO_LOAN" && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Linked Loan</h3>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Loan ID</div>
                  <div className="font-mono font-medium text-gray-900">{application.loan_id}</div>
                </div>
                <div className="bg-white rounded p-3 text-sm">
                  <p className="text-gray-700 mb-2">
                    This application has been approved and converted to a loan. The bicycle has been
                    registered as collateral for the loan.
                  </p>
                </div>
                <div className="flex gap-2">
                  <a
                    href={`#`}
                    className="flex-1 text-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                    onClick={(e) => {
                      e.preventDefault();
                      alert("Loan detail page not yet implemented. Loan ID: " + application.loan_id);
                    }}
                  >
                    View Loan Details
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          {canApproveOrReject && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Application</h3>
              <div className="space-y-4">
                <button
                  onClick={() => setShowApproveDialog(true)}
                  className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
                  disabled={actionLoading}
                >
                  Approve Application
                </button>
                <button
                  onClick={() => setShowRejectDialog(true)}
                  className="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition-colors font-medium"
                  disabled={actionLoading}
                >
                  Reject Application
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Approve Dialog */}
      {showApproveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Approve Application</h3>
            <p className="text-gray-600 mb-4">
              This will create a loan and mark the bicycle as sold. This action cannot be undone.
            </p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes (optional)"
              rows={3}
              className="w-full border rounded-lg px-3 py-2 mb-4 focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <div className="flex gap-3">
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50"
              >
                {actionLoading ? "Processing..." : "Confirm Approval"}
              </button>
              <button
                onClick={() => {
                  setShowApproveDialog(false);
                  setNotes("");
                }}
                disabled={actionLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Reject Application</h3>
            <p className="text-gray-600 mb-4">
              This will release the bicycle reservation and notify the customer.
            </p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Reason for rejection (required)"
              rows={3}
              required
              className="w-full border rounded-lg px-3 py-2 mb-4 focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
            <div className="flex gap-3">
              <button
                onClick={handleReject}
                disabled={actionLoading || !notes.trim()}
                className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
              >
                {actionLoading ? "Processing..." : "Confirm Rejection"}
              </button>
              <button
                onClick={() => {
                  setShowRejectDialog(false);
                  setNotes("");
                }}
                disabled={actionLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
