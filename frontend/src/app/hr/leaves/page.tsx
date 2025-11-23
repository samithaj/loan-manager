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
  approver_id?: string;
  approved_at?: string;
  approver_notes?: string;
  created_at: string;
}

export default function LeaveApplicationsPage() {
  const [applications, setApplications] = useState<LeaveApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: "",
    dateFrom: "",
    dateTo: ""
  });

  useEffect(() => {
    fetchApplications();
  }, [filter]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.status) params.append("status", filter.status);
      if (filter.dateFrom) params.append("from_date", filter.dateFrom);
      if (filter.dateTo) params.append("to_date", filter.dateTo);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/my?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setApplications(data.items || []);
      } else {
        console.error("Failed to fetch leave applications");
      }
    } catch (error) {
      console.error("Error fetching leave applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "DRAFT":
        return "bg-gray-100 text-gray-600";
      case "PENDING":
        return "bg-yellow-100 text-yellow-800";
      case "APPROVED_BRANCH":
        return "bg-blue-100 text-blue-800";
      case "APPROVED_HO":
        return "bg-green-100 text-green-700";
      case "APPROVED":
        return "bg-green-100 text-green-800";
      case "REJECTED":
        return "bg-red-100 text-red-800";
      case "CANCELLED":
        return "bg-gray-100 text-gray-800";
      case "NEEDS_INFO":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "DRAFT":
        return "Draft";
      case "PENDING":
        return "Pending";
      case "APPROVED_BRANCH":
        return "Approved (Branch)";
      case "APPROVED_HO":
        return "Approved (HO)";
      case "APPROVED":
        return "Approved";
      case "REJECTED":
        return "Rejected";
      case "CANCELLED":
        return "Cancelled";
      case "NEEDS_INFO":
        return "Needs Info";
      default:
        return status;
    }
  };

  const cancelApplication = async (applicationId: string) => {
    const reason = prompt("Please provide a reason for cancellation:");
    if (!reason || reason.trim() === "") {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${applicationId}/cancel`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: reason.trim() })
        }
      );

      if (response.ok) {
        alert("Leave application cancelled successfully");
        fetchApplications();
      } else {
        const error = await response.json();
        alert(`Failed to cancel: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error cancelling application:", error);
      alert("An error occurred while cancelling the application");
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">My Leave Applications</h1>
        <div className="flex gap-3">
          <Link
            href="/hr/leaves/balances"
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition"
          >
            View Balances
          </Link>
          <Link
            href="/hr/leaves/apply"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
          >
            Apply for Leave
          </Link>
        </div>
      </div>

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
              <option value="DRAFT">Draft</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED_BRANCH">Approved (Branch)</option>
              <option value="APPROVED_HO">Approved (HO)</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="NEEDS_INFO">Needs Info</option>
              <option value="CANCELLED">Cancelled</option>
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
          <p className="mt-4 text-gray-600">Loading leave applications...</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">No leave applications found</p>
          <Link
            href="/hr/leaves/apply"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition"
          >
            Apply for Leave
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
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
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Applied
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
                      {application.leave_type_name || application.leave_type_id}
                    </div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">
                      {application.reason.substring(0, 60)}
                      {application.reason.length > 60 && "..."}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(application.start_date).toLocaleDateString()} -{" "}
                    {new Date(application.end_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {application.total_days} days
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                        application.status
                      )}`}
                    >
                      {getStatusLabel(application.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(application.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
                    <Link
                      href={`/hr/leaves/${application.id}`}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </Link>
                    {(application.status === "DRAFT" ||
                      application.status === "PENDING" ||
                      application.status === "APPROVED_BRANCH" ||
                      application.status === "APPROVED") && (
                      <button
                        onClick={() => cancelApplication(application.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
