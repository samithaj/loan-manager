"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface RepairJob {
  id: string;
  job_number: string;
  bicycle_id: string;
  bicycle_info?: {
    title: string;
    license_plate: string;
  };
  branch_id: string;
  job_type: string;
  status: string;
  opened_at: string;
  completed_at?: string;
  mechanic_id?: string;
  total_cost: number;
  total_price: number;
}

export default function RepairJobsPage() {
  const [jobs, setJobs] = useState<RepairJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: "",
    jobType: "",
    mechanicId: ""
  });

  useEffect(() => {
    fetchJobs();
  }, [filter]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.status) params.append("status", filter.status);
      if (filter.jobType) params.append("job_type", filter.jobType);
      if (filter.mechanicId) params.append("mechanic_id", filter.mechanicId);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/workshop/jobs?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setJobs(data.items || []);
      }
    } catch (error) {
      console.error("Error fetching repair jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD"
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      OPEN: "bg-yellow-100 text-yellow-800",
      IN_PROGRESS: "bg-blue-100 text-blue-800",
      COMPLETED: "bg-green-100 text-green-800",
      INVOICED: "bg-purple-100 text-purple-800",
      CANCELLED: "bg-red-100 text-red-800"
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  const getJobTypeLabel = (jobType: string) => {
    const labels: Record<string, string> = {
      SERVICE: "Service",
      ACCIDENT_REPAIR: "Accident Repair",
      FULL_OVERHAUL_BEFORE_SALE: "Full Overhaul (Pre-Sale)",
      MAINTENANCE: "Maintenance",
      CUSTOM_WORK: "Custom Work",
      WARRANTY_REPAIR: "Warranty Repair"
    };
    return labels[jobType] || jobType;
  };

  const calculateMargin = (cost: number, price: number) => {
    if (price === 0) return 0;
    return ((price - cost) / price) * 100;
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Repair Jobs</h1>
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
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="INVOICED">Invoiced</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Job Type
            </label>
            <select
              value={filter.jobType}
              onChange={(e) => setFilter({ ...filter, jobType: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="SERVICE">Service</option>
              <option value="ACCIDENT_REPAIR">Accident Repair</option>
              <option value="FULL_OVERHAUL_BEFORE_SALE">Full Overhaul (Pre-Sale)</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="CUSTOM_WORK">Custom Work</option>
              <option value="WARRANTY_REPAIR">Warranty Repair</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading repair jobs...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No repair jobs found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-gray-900">
                      {job.job_number}
                    </h3>
                    <span
                      className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(
                        job.status
                      )}`}
                    >
                      {job.status}
                    </span>
                  </div>
                  {job.bicycle_info && (
                    <div className="text-sm text-gray-600">
                      <span className="font-semibold">{job.bicycle_info.title}</span> •{" "}
                      {job.bicycle_info.license_plate}
                    </div>
                  )}
                  <div className="text-sm text-gray-500 mt-1">
                    {getJobTypeLabel(job.job_type)} • Opened:{" "}
                    {new Date(job.opened_at).toLocaleDateString()}
                    {job.completed_at && (
                      <> • Completed: {new Date(job.completed_at).toLocaleDateString()}</>
                    )}
                  </div>
                </div>
                <Link
                  href={`/workshop/jobs/${job.id}`}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
                >
                  View Details
                </Link>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-500">Internal Cost</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {formatCurrency(job.total_cost)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Customer Price</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {formatCurrency(job.total_price)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Margin</div>
                  <div className="text-lg font-semibold text-green-600">
                    {calculateMargin(job.total_cost, job.total_price).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Profit</div>
                  <div className="text-lg font-semibold text-green-600">
                    {formatCurrency(job.total_price - job.total_cost)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      {jobs.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{jobs.length}</div>
              <div className="text-sm text-gray-500">Total Jobs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {jobs.filter((j) => j.status === "OPEN" || j.status === "IN_PROGRESS").length}
              </div>
              <div className="text-sm text-gray-500">Active Jobs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {formatCurrency(jobs.reduce((sum, j) => sum + j.total_cost, 0))}
              </div>
              <div className="text-sm text-gray-500">Total Cost</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(
                  jobs.reduce((sum, j) => sum + (j.total_price - j.total_cost), 0)
                )}
              </div>
              <div className="text-sm text-gray-500">Total Profit</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
