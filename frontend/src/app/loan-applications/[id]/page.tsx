"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface Application {
  id: string;
  application_no: string;
  status: string;
  requested_amount: number;
  tenure_months: number;
  lmo_notes?: string;
  created_at: string;
  submitted_at?: string;
  customer?: {
    full_name: string;
    nic: string;
    dob?: string;
    address: string;
    phone: string;
    email?: string;
  };
  vehicle?: {
    make: string;
    model: string;
    chassis_no: string;
    engine_no?: string;
    year?: number;
    color?: string;
    registration_no?: string;
  };
  branch?: {
    name: string;
    code: string;
  };
  documents?: any[];
  decisions?: any[];
}

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  actor?: string;
  description: string;
  details?: any;
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-200 text-gray-800",
  SUBMITTED: "bg-blue-200 text-blue-800",
  UNDER_REVIEW: "bg-yellow-200 text-yellow-800",
  NEEDS_MORE_INFO: "bg-orange-200 text-orange-800",
  APPROVED: "bg-green-200 text-green-800",
  REJECTED: "bg-red-200 text-red-800",
  CANCELLED: "bg-gray-300 text-gray-600",
};

export default function LoanApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [application, setApplication] = useState<Application | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"details" | "documents" | "timeline">("details");

  useEffect(() => {
    if (params.id) {
      fetchApplication();
      fetchTimeline();
    }
  }, [params.id]);

  const fetchApplication = async () => {
    try {
      const response = await fetch(`/api/v1/loan-applications/${params.id}`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setApplication(data);
      }
    } catch (error) {
      console.error("Failed to fetch application:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTimeline = async () => {
    try {
      const response = await fetch(`/api/v1/loan-applications/${params.id}/timeline`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setTimeline(data.events);
      }
    } catch (error) {
      console.error("Failed to fetch timeline:", error);
    }
  };

  const handleSubmit = async () => {
    if (!confirm("Are you sure you want to submit this application?")) return;

    try {
      const response = await fetch(`/api/v1/loan-applications/${params.id}/submit`, {
        method: "POST",
        credentials: "include",
      });
      if (response.ok) {
        fetchApplication();
        fetchTimeline();
      }
    } catch (error) {
      console.error("Failed to submit application:", error);
      alert("Failed to submit application");
    }
  };

  const handleCancel = async () => {
    const reason = prompt("Enter reason for cancellation:");
    if (!reason) return;

    try {
      const response = await fetch(
        `/api/v1/loan-applications/${params.id}/cancel?reason=${encodeURIComponent(reason)}`,
        {
          method: "POST",
          credentials: "include",
        }
      );
      if (response.ok) {
        fetchApplication();
        fetchTimeline();
      }
    } catch (error) {
      console.error("Failed to cancel application:", error);
      alert("Failed to cancel application");
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (!application) {
    return <div className="container mx-auto px-4 py-8">Application not found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <Link href="/loan-applications" className="text-blue-600 hover:underline mb-2 inline-block">
            ← Back to Applications
          </Link>
          <h1 className="text-3xl font-bold">{application.application_no}</h1>
          <p className="text-gray-600 mt-1">
            Created {new Date(application.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className={`px-4 py-2 rounded-full font-semibold ${STATUS_COLORS[application.status]}`}>
            {application.status.replace("_", " ")}
          </span>
          {application.status === "DRAFT" && (
            <button
              onClick={handleSubmit}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Submit for Review
            </button>
          )}
          {!["APPROVED", "REJECTED", "CANCELLED"].includes(application.status) && (
            <button
              onClick={handleCancel}
              className="border border-red-600 text-red-600 px-4 py-2 rounded hover:bg-red-50"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab("details")}
            className={`pb-2 ${
              activeTab === "details"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600"
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab("documents")}
            className={`pb-2 ${
              activeTab === "documents"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600"
            }`}
          >
            Documents ({application.documents?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`pb-2 ${
              activeTab === "timeline"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600"
            }`}
          >
            Timeline
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "details" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Loan Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Loan Details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-600">Branch</dt>
                <dd className="font-medium">{application.branch?.name}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Requested Amount</dt>
                <dd className="font-medium">Rs. {application.requested_amount.toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Tenure</dt>
                <dd className="font-medium">
                  {application.tenure_months} months ({(application.tenure_months / 12).toFixed(1)} years)
                </dd>
              </div>
              {application.lmo_notes && (
                <div>
                  <dt className="text-sm text-gray-600">Notes</dt>
                  <dd className="text-sm">{application.lmo_notes}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Customer Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-600">Full Name</dt>
                <dd className="font-medium">{application.customer?.full_name}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">NIC</dt>
                <dd className="font-medium">{application.customer?.nic}</dd>
              </div>
              {application.customer?.dob && (
                <div>
                  <dt className="text-sm text-gray-600">Date of Birth</dt>
                  <dd className="font-medium">
                    {new Date(application.customer.dob).toLocaleDateString()}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-sm text-gray-600">Address</dt>
                <dd className="text-sm">{application.customer?.address}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Phone</dt>
                <dd className="font-medium">{application.customer?.phone}</dd>
              </div>
              {application.customer?.email && (
                <div>
                  <dt className="text-sm text-gray-600">Email</dt>
                  <dd className="font-medium">{application.customer.email}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Vehicle Details */}
          <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Vehicle Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm text-gray-600">Make/Model</dt>
                <dd className="font-medium">
                  {application.vehicle?.make} {application.vehicle?.model}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Chassis Number</dt>
                <dd className="font-medium">{application.vehicle?.chassis_no}</dd>
              </div>
              {application.vehicle?.engine_no && (
                <div>
                  <dt className="text-sm text-gray-600">Engine Number</dt>
                  <dd className="font-medium">{application.vehicle.engine_no}</dd>
                </div>
              )}
              {application.vehicle?.year && (
                <div>
                  <dt className="text-sm text-gray-600">Year</dt>
                  <dd className="font-medium">{application.vehicle.year}</dd>
                </div>
              )}
              {application.vehicle?.color && (
                <div>
                  <dt className="text-sm text-gray-600">Color</dt>
                  <dd className="font-medium">{application.vehicle.color}</dd>
                </div>
              )}
              {application.vehicle?.registration_no && (
                <div>
                  <dt className="text-sm text-gray-600">Registration No</dt>
                  <dd className="font-medium">{application.vehicle.registration_no}</dd>
                </div>
              )}
            </div>
          </div>

          {/* Decisions */}
          {application.decisions && application.decisions.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
              <h2 className="text-xl font-semibold mb-4">Decisions</h2>
              <div className="space-y-4">
                {application.decisions.map((decision: any) => (
                  <div key={decision.id} className="border-l-4 border-blue-600 pl-4">
                    <div className="flex justify-between">
                      <div className="font-semibold">{decision.decision}</div>
                      <div className="text-sm text-gray-600">
                        {new Date(decision.decided_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-sm mt-2">{decision.notes}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "documents" && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Documents</h2>
            {["DRAFT", "NEEDS_MORE_INFO"].includes(application.status) && (
              <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                Upload Document
              </button>
            )}
          </div>
          {!application.documents || application.documents.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No documents uploaded</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {application.documents.map((doc: any) => (
                <div key={doc.id} className="border rounded p-4">
                  <div className="font-medium">{doc.doc_type.replace("_", " ")}</div>
                  <div className="text-sm text-gray-600 mt-1">{doc.file_name}</div>
                  <div className="text-xs text-gray-500">
                    {(doc.file_size / 1024).toFixed(1)} KB
                  </div>
                  <button className="text-blue-600 text-sm mt-2">View</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "timeline" && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Timeline</h2>
          <div className="space-y-4">
            {timeline.map((event, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0 w-2 bg-blue-600 rounded" />
                <div className="flex-1 pb-4">
                  <div className="flex justify-between">
                    <div className="font-medium">{event.description}</div>
                    <div className="text-sm text-gray-600">
                      {new Date(event.timestamp).toLocaleString()}
                    </div>
                  </div>
                  {event.actor && (
                    <div className="text-sm text-gray-600 mt-1">by {event.actor}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
