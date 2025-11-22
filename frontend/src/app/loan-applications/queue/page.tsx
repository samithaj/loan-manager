"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Application {
  id: string;
  application_no: string;
  status: string;
  requested_amount: number;
  tenure_months: number;
  customer?: {
    full_name: string;
    nic: string;
  };
  vehicle?: {
    make: string;
    model: string;
  };
  branch?: {
    name: string;
  };
  submitted_at?: string;
  created_at: string;
}

interface QueueStats {
  submitted: number;
  under_review: number;
  needs_more_info: number;
  approved: number;
  rejected: number;
}

export default function LoanApprovalQueuePage() {
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<QueueStats>({
    submitted: 0,
    under_review: 0,
    needs_more_info: 0,
    approved: 0,
    rejected: 0,
  });
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<string>("SUBMITTED");
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED" | "NEEDS_MORE_INFO" | null>(null);
  const [notes, setNotes] = useState<string>("");
  const [showDecisionModal, setShowDecisionModal] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchApplications();
  }, [activeFilter]);

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/v1/loan-applications/stats/queue", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        status: activeFilter,
        page: "1",
        page_size: "50",
      });

      const response = await fetch(`/api/v1/loan-applications?${params}`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setApplications(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartReview = async (app: Application) => {
    try {
      const response = await fetch(`/api/v1/loan-applications/${app.id}/start-review`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        router.push(`/loan-applications/${app.id}`);
      }
    } catch (error) {
      console.error("Failed to start review:", error);
    }
  };

  const handleDecision = (app: Application, decisionType: "APPROVED" | "REJECTED" | "NEEDS_MORE_INFO") => {
    setSelectedApp(app);
    setDecision(decisionType);
    setNotes("");
    setShowDecisionModal(true);
  };

  const submitDecision = async () => {
    if (!selectedApp || !decision || !notes.trim()) {
      alert("Please provide notes for your decision");
      return;
    }

    try {
      const response = await fetch(`/api/v1/loan-applications/${selectedApp.id}/decision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          decision,
          notes,
        }),
      });

      if (response.ok) {
        setShowDecisionModal(false);
        fetchStats();
        fetchApplications();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error("Failed to submit decision:", error);
      alert("Failed to submit decision");
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <h1 className="text-3xl font-bold mb-6">Loan Approval Queue</h1>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div
          onClick={() => setActiveFilter("SUBMITTED")}
          className={`bg-white rounded-lg shadow p-4 cursor-pointer ${
            activeFilter === "SUBMITTED" ? "ring-2 ring-blue-600" : ""
          }`}
        >
          <div className="text-3xl font-bold text-blue-600">{stats.submitted}</div>
          <div className="text-sm text-gray-600">Submitted</div>
        </div>

        <div
          onClick={() => setActiveFilter("UNDER_REVIEW")}
          className={`bg-white rounded-lg shadow p-4 cursor-pointer ${
            activeFilter === "UNDER_REVIEW" ? "ring-2 ring-blue-600" : ""
          }`}
        >
          <div className="text-3xl font-bold text-yellow-600">{stats.under_review}</div>
          <div className="text-sm text-gray-600">Under Review</div>
        </div>

        <div
          onClick={() => setActiveFilter("NEEDS_MORE_INFO")}
          className={`bg-white rounded-lg shadow p-4 cursor-pointer ${
            activeFilter === "NEEDS_MORE_INFO" ? "ring-2 ring-blue-600" : ""
          }`}
        >
          <div className="text-3xl font-bold text-orange-600">{stats.needs_more_info}</div>
          <div className="text-sm text-gray-600">Needs Info</div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-3xl font-bold text-green-600">{stats.approved}</div>
          <div className="text-sm text-gray-600">Approved Today</div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-3xl font-bold text-red-600">{stats.rejected}</div>
          <div className="text-sm text-gray-600">Rejected Today</div>
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : applications.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No applications in this queue
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  App No
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Vehicle
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Branch
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Submitted
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {applications.map((app) => (
                <tr key={app.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    <Link
                      href={`/loan-applications/${app.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      {app.application_no}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium">{app.customer?.full_name}</div>
                      <div className="text-sm text-gray-500">{app.customer?.nic}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {app.vehicle?.make} {app.vehicle?.model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    Rs. {app.requested_amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">{app.branch?.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {app.submitted_at
                      ? new Date(app.submitted_at).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex gap-2">
                      {app.status === "SUBMITTED" && (
                        <button
                          onClick={() => handleStartReview(app)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Start Review
                        </button>
                      )}
                      {app.status === "UNDER_REVIEW" && (
                        <>
                          <button
                            onClick={() => handleDecision(app, "APPROVED")}
                            className="text-green-600 hover:text-green-800"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleDecision(app, "REJECTED")}
                            className="text-red-600 hover:text-red-800"
                          >
                            Reject
                          </button>
                          <button
                            onClick={() => handleDecision(app, "NEEDS_MORE_INFO")}
                            className="text-orange-600 hover:text-orange-800"
                          >
                            Request Info
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

      {/* Decision Modal */}
      {showDecisionModal && selectedApp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">
              {decision === "APPROVED" && "Approve Application"}
              {decision === "REJECTED" && "Reject Application"}
              {decision === "NEEDS_MORE_INFO" && "Request More Information"}
            </h2>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Application: {selectedApp.application_no}
              </p>
              <p className="text-sm text-gray-600">
                Customer: {selectedApp.customer?.full_name}
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                {decision === "NEEDS_MORE_INFO" ? "Details Required" : "Decision Notes"}*
              </label>
              <textarea
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                placeholder={
                  decision === "NEEDS_MORE_INFO"
                    ? "Specify what additional information is needed..."
                    : "Provide reason for your decision..."
                }
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDecisionModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={submitDecision}
                disabled={!notes.trim()}
                className={`px-4 py-2 rounded text-white disabled:opacity-50 ${
                  decision === "APPROVED"
                    ? "bg-green-600 hover:bg-green-700"
                    : decision === "REJECTED"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-orange-600 hover:bg-orange-700"
                }`}
              >
                Submit {decision === "APPROVED" ? "Approval" : decision === "REJECTED" ? "Rejection" : "Request"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
