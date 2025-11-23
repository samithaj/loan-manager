"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface LeaveApplication {
  id: string;
  user_id: string;
  leave_type_id: string;
  leave_type_name?: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason: string;
  status: string;
  is_half_day: boolean;
  employee_name?: string;
  employee_email?: string;
  branch_name?: string;
  branch_approver_name?: string;
  branch_approved_at?: string;
  created_at: string;
}

interface DashboardStats {
  pending_approvals: number;
  approved_this_month: number;
  rejected_this_month: number;
  needs_info_count: number;
}

export default function HeadOfficeQueuePage() {
  const [applications, setApplications] = useState<LeaveApplication[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<LeaveApplication | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [actionType, setActionType] = useState<"approve" | "reject" | "info" | null>(null);
  const [actionNotes, setActionNotes] = useState("");
  const [processing, setProcessing] = useState(false);
  const [filter, setFilter] = useState({
    status: "APPROVED_BRANCH",
    branch_id: "",
    dateFrom: "",
    dateTo: "",
  });

  useEffect(() => {
    fetchQueue();
    fetchStats();
  }, [filter]);

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.status) params.append("status", filter.status);
      if (filter.branch_id) params.append("branch_id", filter.branch_id);
      if (filter.dateFrom) params.append("from_date", filter.dateFrom);
      if (filter.dateTo) params.append("to_date", filter.dateTo);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/queue/head-office?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setApplications(data.items || []);
      } else {
        console.error("Failed to fetch HO approval queue");
      }
    } catch (error) {
      console.error("Error fetching HO approval queue:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/dashboard/stats`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const openApprovalModal = (
    app: LeaveApplication,
    action: "approve" | "reject" | "info"
  ) => {
    setSelectedApp(app);
    setActionType(action);
    setActionNotes("");
    setShowApprovalModal(true);
  };

  const handleApprove = async () => {
    if (!selectedApp) return;

    setProcessing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${selectedApp.id}/approve-ho`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes: actionNotes || undefined }),
        }
      );

      if (response.ok) {
        alert("Leave application approved successfully");
        setShowApprovalModal(false);
        fetchQueue();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`Failed to approve: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error approving application:", error);
      alert("An error occurred while approving the application");
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedApp || !actionNotes.trim()) {
      alert("Please provide a reason for rejection");
      return;
    }

    setProcessing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${selectedApp.id}/reject`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes: actionNotes }),
        }
      );

      if (response.ok) {
        alert("Leave application rejected");
        setShowApprovalModal(false);
        fetchQueue();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`Failed to reject: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error rejecting application:", error);
      alert("An error occurred while rejecting the application");
    } finally {
      setProcessing(false);
    }
  };

  const handleRequestInfo = async () => {
    if (!selectedApp || !actionNotes.trim()) {
      alert("Please provide details about what information is needed");
      return;
    }

    setProcessing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${selectedApp.id}/request-info`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes: actionNotes }),
        }
      );

      if (response.ok) {
        alert("Information request sent to employee");
        setShowApprovalModal(false);
        fetchQueue();
        fetchStats();
      } else {
        const error = await response.json();
        alert(`Failed to request info: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error requesting info:", error);
      alert("An error occurred while requesting information");
    } finally {
      setProcessing(false);
    }
  };

  const handleModalAction = () => {
    if (actionType === "approve") {
      handleApprove();
    } else if (actionType === "reject") {
      handleReject();
    } else if (actionType === "info") {
      handleRequestInfo();
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED_BRANCH":
        return "bg-blue-100 text-blue-800";
      case "PENDING":
        return "bg-yellow-100 text-yellow-800";
      case "NEEDS_INFO":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Head Office - Leave Approvals
        </h1>
        <p className="mt-2 text-gray-600">
          Final approval for leave requests requiring Head Office authorization
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm font-medium text-gray-500">Pending HO Approvals</div>
            <div className="mt-1 text-3xl font-semibold text-blue-600">
              {stats.pending_approvals}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm font-medium text-gray-500">Approved This Month</div>
            <div className="mt-1 text-3xl font-semibold text-green-600">
              {stats.approved_this_month}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm font-medium text-gray-500">Rejected This Month</div>
            <div className="mt-1 text-3xl font-semibold text-red-600">
              {stats.rejected_this_month}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm font-medium text-gray-500">Needs Info</div>
            <div className="mt-1 text-3xl font-semibold text-orange-600">
              {stats.needs_info_count}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="APPROVED_BRANCH">Pending HO Approval</option>
              <option value="PENDING">All Pending</option>
              <option value="NEEDS_INFO">Needs Info</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Date
            </label>
            <input
              type="date"
              value={filter.dateFrom}
              onChange={(e) => setFilter({ ...filter, dateFrom: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Date
            </label>
            <input
              type="date"
              value={filter.dateTo}
              onChange={(e) => setFilter({ ...filter, dateTo: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading HO approval queue...</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No leave applications pending HO approval</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Branch
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Leave Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Days
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Branch Approval
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {applications.map((application) => (
                <tr key={application.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {application.employee_name || "Unknown"}
                    </div>
                    <div className="text-sm text-gray-500">
                      {application.employee_email}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {application.branch_name || "N/A"}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {application.leave_type_name || application.leave_type_id}
                    </div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">
                      {application.reason.substring(0, 50)}
                      {application.reason.length > 50 && "..."}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(application.start_date).toLocaleDateString()} -{" "}
                    {new Date(application.end_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {application.total_days} day{application.total_days !== 1 ? "s" : ""}
                    {application.is_half_day && <span className="text-gray-500"> (Half)</span>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {application.branch_approver_name || "N/A"}
                    </div>
                    {application.branch_approved_at && (
                      <div className="text-xs text-gray-500">
                        {new Date(application.branch_approved_at).toLocaleDateString()}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <Link
                      href={`/hr/leaves/${application.id}`}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </Link>
                    {application.status === "APPROVED_BRANCH" && (
                      <>
                        <button
                          onClick={() => openApprovalModal(application, "approve")}
                          className="text-green-600 hover:text-green-900"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => openApprovalModal(application, "reject")}
                          className="text-red-600 hover:text-red-900"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => openApprovalModal(application, "info")}
                          className="text-orange-600 hover:text-orange-900"
                        >
                          Request Info
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Approval Modal */}
      {showApprovalModal && selectedApp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {actionType === "approve" && "Approve Leave Request (Head Office)"}
                {actionType === "reject" && "Reject Leave Request"}
                {actionType === "info" && "Request More Information"}
              </h3>
            </div>

            <div className="px-6 py-4">
              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-2">Employee</div>
                <div className="text-base font-medium">{selectedApp.employee_name}</div>
                <div className="text-sm text-gray-500">{selectedApp.branch_name}</div>
              </div>

              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-2">Leave Period</div>
                <div className="text-base">
                  {new Date(selectedApp.start_date).toLocaleDateString()} -{" "}
                  {new Date(selectedApp.end_date).toLocaleDateString()} (
                  {selectedApp.total_days} days)
                </div>
              </div>

              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-2">Reason</div>
                <div className="text-base">{selectedApp.reason}</div>
              </div>

              {selectedApp.branch_approver_name && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm font-medium text-blue-900">Branch Approval</div>
                  <div className="text-sm text-blue-700 mt-1">
                    Approved by {selectedApp.branch_approver_name} on{" "}
                    {selectedApp.branch_approved_at &&
                      new Date(selectedApp.branch_approved_at).toLocaleDateString()}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {actionType === "approve" && "Notes (Optional)"}
                  {actionType === "reject" && "Reason for Rejection *"}
                  {actionType === "info" && "What information is needed? *"}
                </label>
                <textarea
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder={
                    actionType === "approve"
                      ? "Add any notes (optional)..."
                      : "Please provide a reason..."
                  }
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowApprovalModal(false)}
                disabled={processing}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleModalAction}
                disabled={processing}
                className={`px-4 py-2 rounded-lg text-white transition disabled:opacity-50 ${
                  actionType === "approve"
                    ? "bg-green-600 hover:bg-green-700"
                    : actionType === "reject"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-orange-600 hover:bg-orange-700"
                }`}
              >
                {processing
                  ? "Processing..."
                  : actionType === "approve"
                  ? "Approve"
                  : actionType === "reject"
                  ? "Reject"
                  : "Request Info"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
