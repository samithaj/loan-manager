"use client";
import { useEffect, useState } from "react";

type Job = {
  id: string;
  type: string;
  status: string;
  createdOn: string;
  startedOn?: string | null;
  completedOn?: string | null;
  totalRecords?: number | null;
  processedRecords?: number | null;
  successCount?: number | null;
  errorCount?: number | null;
  errorDetails?: string | null;
  resultData?: string | null;
};

interface JobStatusMonitorProps {
  jobId: string;
  onComplete?: () => void;
}

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function JobStatusMonitor({ jobId, onComplete }: JobStatusMonitorProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadJob() {
    try {
      const res = await fetch(`${base}/v1/jobs/${jobId}`, {
        cache: "no-store",
        headers: authHeaders()
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Job;
      setJob(data);
      
      // If job is complete, stop polling
      if (data.status === "SUCCEEDED" || data.status === "FAILED") {
        setLoading(false);
        if (onComplete) {
          setTimeout(onComplete, 3000); // Auto-remove after 3 seconds
        }
      }
    } catch {
      setError("Failed to load job status");
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJob();
    
    // Poll for updates if job is not complete
    const interval = setInterval(() => {
      if (job?.status === "PENDING" || job?.status === "RUNNING") {
        loadJob();
      }
    }, 2000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, job?.status]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!job) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse">Loading job status...</div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-yellow-100 text-yellow-800";
      case "RUNNING": return "bg-blue-100 text-blue-800";
      case "SUCCEEDED": return "bg-green-100 text-green-800";
      case "FAILED": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getProgress = () => {
    if (!job.totalRecords || job.totalRecords === 0) return 0;
    return ((job.processedRecords || 0) / job.totalRecords) * 100;
  };

  const formatJobType = (type: string) => {
    return type.replace("BULK_", "").toLowerCase().replace(/^\w/, c => c.toUpperCase());
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium">
            {formatJobType(job.type)} Upload
          </h3>
          <p className="text-sm text-gray-500">Job ID: {job.id}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
          {job.status}
        </span>
      </div>

      {/* Progress Bar */}
      {job.totalRecords && job.totalRecords > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{job.processedRecords || 0} / {job.totalRecords}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgress()}%` }}
            />
          </div>
        </div>
      )}

      {/* Results */}
      {job.status === "SUCCEEDED" || job.status === "FAILED" ? (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Records:</span>
              <span className="ml-2 font-medium">{job.totalRecords || 0}</span>
            </div>
            <div>
              <span className="text-gray-600">Processed:</span>
              <span className="ml-2 font-medium">{job.processedRecords || 0}</span>
            </div>
            <div>
              <span className="text-gray-600">Successful:</span>
              <span className="ml-2 font-medium text-green-600">{job.successCount || 0}</span>
            </div>
            <div>
              <span className="text-gray-600">Errors:</span>
              <span className="ml-2 font-medium text-red-600">{job.errorCount || 0}</span>
            </div>
          </div>

          {job.errorDetails && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-red-600 hover:text-red-800">
                View Error Details
              </summary>
              <div className="mt-2 bg-red-50 border border-red-200 rounded p-3">
                <pre className="text-xs text-red-700 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(JSON.parse(job.errorDetails), null, 2)}
                </pre>
              </div>
            </details>
          )}

          <div className="text-xs text-gray-500 mt-2">
            Completed: {job.completedOn ? new Date(job.completedOn).toLocaleString() : "—"}
          </div>
        </div>
      ) : (
        <div className="text-sm text-gray-600">
          {job.status === "PENDING" ? "Waiting to start..." : "Processing..."}
        </div>
      )}
    </div>
  );
}