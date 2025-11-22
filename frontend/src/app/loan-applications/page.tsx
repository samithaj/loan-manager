"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface LoanApplication {
  id: string;
  application_no: string;
  customer?: {
    full_name: string;
    nic: string;
  };
  vehicle?: {
    make: string;
    model: string;
    chassis_no: string;
  };
  requested_amount: number;
  tenure_months: number;
  status: string;
  branch?: {
    name: string;
  };
  created_at: string;
  submitted_at?: string;
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

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under Review",
  NEEDS_MORE_INFO: "Needs More Info",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  CANCELLED: "Cancelled",
};

export default function LoanApplicationsPage() {
  const router = useRouter();
  const [applications, setApplications] = useState<LoanApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchApplications();
  }, [statusFilter, page]);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
      });

      if (statusFilter) {
        params.append("status", statusFilter);
      }

      if (searchQuery) {
        params.append("application_no", searchQuery);
      }

      const response = await fetch(`/api/v1/loan-applications?${params}`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setApplications(data.items);
        setTotalPages(data.total_pages);
      }
    } catch (error) {
      console.error("Failed to fetch applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchApplications();
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Loan Applications</h1>
        <Link
          href="/loan-applications/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          New Application
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by application number, NIC, chassis no..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border rounded"
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 border rounded"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="NEEDS_MORE_INFO">Needs More Info</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
          <button
            type="submit"
            className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
          >
            Search
          </button>
        </form>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : applications.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No applications found
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Application No
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
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
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
                      {app.application_no}
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium">{app.customer?.full_name}</div>
                        <div className="text-sm text-gray-500">{app.customer?.nic}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div>{app.vehicle?.make} {app.vehicle?.model}</div>
                        <div className="text-sm text-gray-500">
                          {app.vehicle?.chassis_no}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      Rs. {app.requested_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          STATUS_COLORS[app.status]
                        }`}
                      >
                        {STATUS_LABELS[app.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(app.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/loan-applications/${app.id}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
