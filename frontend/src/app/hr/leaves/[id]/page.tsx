"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface LeaveApplication {
  id: string;
  user_id: string;
  leave_type_id: string;
  leave_type_name?: string;
  leave_type_code?: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason: string;
  status: string;
  is_half_day: boolean;
  document_url?: string;
  employee_name?: string;
  employee_email?: string;
  branch_name?: string;
  branch_approver_id?: string;
  branch_approver_name?: string;
  branch_approved_at?: string;
  ho_approver_id?: string;
  ho_approver_name?: string;
  ho_approved_at?: string;
  approver_notes?: string;
  created_at: string;
  updated_at: string;
  can_submit: boolean;
  can_cancel: boolean;
}

interface TimelineEntry {
  id: string;
  action: string;
  actor_id: string;
  actor_name?: string;
  old_status?: string;
  new_status?: string;
  notes?: string;
  created_at: string;
}

export default function LeaveDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leaveId = params?.id as string;

  const [application, setApplication] = useState<LeaveApplication | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"details" | "timeline">("details");

  useEffect(() => {
    if (leaveId) {
      fetchLeaveDetails();
      fetchTimeline();
    }
  }, [leaveId]);

  const fetchLeaveDetails = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${leaveId}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setApplication(data);
      } else {
        console.error("Failed to fetch leave details");
      }
    } catch (error) {
      console.error("Error fetching leave details:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTimeline = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${leaveId}/timeline`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setTimeline(data.timeline || []);
      }
    } catch (error) {
      console.error("Error fetching timeline:", error);
    }
  };

  const cancelApplication = async () => {
    const reason = prompt("Please provide a reason for cancellation:");
    if (!reason || reason.trim() === "") {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${leaveId}/cancel`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: reason.trim() }),
        }
      );

      if (response.ok) {
        alert("Leave application cancelled successfully");
        router.push("/hr/leaves");
      } else {
        const error = await response.json();
        alert(`Failed to cancel: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error cancelling application:", error);
      alert("An error occurred while cancelling the application");
    }
  };

  const submitApplication = async () => {
    if (!confirm("Are you sure you want to submit this leave application for approval?")) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave-approval/applications/${leaveId}/submit`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (response.ok) {
        alert("Leave application submitted successfully");
        fetchLeaveDetails();
        fetchTimeline();
      } else {
        const error = await response.json();
        alert(`Failed to submit: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error submitting application:", error);
      alert("An error occurred while submitting the application");
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
        return "Pending Approval";
      case "APPROVED_BRANCH":
        return "Approved by Branch Manager";
      case "APPROVED_HO":
        return "Approved by Head Office";
      case "APPROVED":
        return "Fully Approved";
      case "REJECTED":
        return "Rejected";
      case "CANCELLED":
        return "Cancelled";
      case "NEEDS_INFO":
        return "More Information Needed";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading leave application...</p>
        </div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">Leave application not found</p>
          <Link
            href="/hr/leaves"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition"
          >
            Back to My Leaves
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/hr/leaves"
          className="text-blue-600 hover:text-blue-800 mb-2 inline-block"
        >
          ← Back to My Leaves
        </Link>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Leave Application</h1>
            <p className="text-gray-500 mt-1">ID: {application.id}</p>
          </div>
          <div className="flex gap-3">
            {application.can_submit && (
              <button
                onClick={submitApplication}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
              >
                Submit for Approval
              </button>
            )}
            {application.can_cancel && (
              <button
                onClick={cancelApplication}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition"
              >
                Cancel Application
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span
          className={`px-4 py-2 inline-flex text-sm font-semibold rounded-full ${getStatusColor(
            application.status
          )}`}
        >
          {getStatusLabel(application.status)}
        </span>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab("details")}
            className={`${
              activeTab === "details"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`${
              activeTab === "timeline"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Timeline
          </button>
        </nav>
      </div>

      {/* Details Tab */}
      {activeTab === "details" && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Leave Details</h2>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500">Leave Type</label>
                <p className="mt-1 text-base text-gray-900">
                  {application.leave_type_name || application.leave_type_id}
                  {application.leave_type_code && (
                    <span className="ml-2 text-gray-500 text-sm">({application.leave_type_code})</span>
                  )}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Branch</label>
                <p className="mt-1 text-base text-gray-900">{application.branch_name || "N/A"}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Start Date</label>
                <p className="mt-1 text-base text-gray-900">
                  {new Date(application.start_date).toLocaleDateString()}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">End Date</label>
                <p className="mt-1 text-base text-gray-900">
                  {new Date(application.end_date).toLocaleDateString()}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Total Days</label>
                <p className="mt-1 text-base text-gray-900">
                  {application.total_days} day{application.total_days !== 1 ? "s" : ""}
                  {application.is_half_day && <span className="text-gray-500"> (Half Day)</span>}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Applied On</label>
                <p className="mt-1 text-base text-gray-900">
                  {new Date(application.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500">Reason</label>
              <p className="mt-1 text-base text-gray-900">{application.reason}</p>
            </div>

            {application.document_url && (
              <div>
                <label className="block text-sm font-medium text-gray-500">Document</label>
                <a
                  href={application.document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 text-blue-600 hover:text-blue-800"
                >
                  View Document
                </a>
              </div>
            )}

            {/* Approval Information */}
            {application.branch_approver_name && (
              <div className="border-t border-gray-200 pt-4 mt-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Approval Information</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Branch Manager</label>
                    <p className="mt-1 text-base text-gray-900">{application.branch_approver_name}</p>
                    {application.branch_approved_at && (
                      <p className="text-sm text-gray-500">
                        Approved on {new Date(application.branch_approved_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                  {application.ho_approver_name && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Head Office Manager</label>
                      <p className="mt-1 text-base text-gray-900">{application.ho_approver_name}</p>
                      {application.ho_approved_at && (
                        <p className="text-sm text-gray-500">
                          Approved on {new Date(application.ho_approved_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}
                  {application.approver_notes && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Approver Notes</label>
                      <p className="mt-1 text-base text-gray-900">{application.approver_notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === "timeline" && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Application Timeline</h2>
          </div>
          <div className="px-6 py-4">
            {timeline.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No timeline events yet</p>
            ) : (
              <div className="flow-root">
                <ul className="-mb-8">
                  {timeline.map((event, eventIdx) => (
                    <li key={event.id}>
                      <div className="relative pb-8">
                        {eventIdx !== timeline.length - 1 && (
                          <span
                            className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                            aria-hidden="true"
                          ></span>
                        )}
                        <div className="relative flex space-x-3">
                          <div>
                            <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                              <span className="text-white text-xs font-medium">
                                {event.action.substring(0, 1)}
                              </span>
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                            <div>
                              <p className="text-sm text-gray-900 font-medium">
                                {event.action.replace(/_/g, " ")}
                              </p>
                              <p className="text-sm text-gray-500">
                                by {event.actor_name || "Unknown"}
                              </p>
                              {event.old_status && event.new_status && (
                                <p className="text-xs text-gray-500 mt-1">
                                  {event.old_status} → {event.new_status}
                                </p>
                              )}
                              {event.notes && (
                                <p className="text-sm text-gray-700 mt-2 italic">"{event.notes}"</p>
                              )}
                            </div>
                            <div className="text-right text-sm whitespace-nowrap text-gray-500">
                              <time dateTime={event.created_at}>
                                {new Date(event.created_at).toLocaleString()}
                              </time>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
