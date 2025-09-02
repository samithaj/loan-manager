"use client";
import { useState, useCallback } from "react";
import JobStatusMonitor from "./JobStatusMonitor";

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

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function BulkUploadManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [activeJobs, setActiveJobs] = useState<Job[]>([]);
  const [uploading, setUploading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = useCallback(async (file: File, uploadType: "clients" | "loans") => {
    if (!file.name.endsWith('.csv')) {
      setError("Please upload a CSV file");
      return;
    }

    setUploading(uploadType);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${base}/v1/bulk/${uploadType}`, {
        method: "POST",
        headers: authHeaders(),
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Upload failed: ${res.status}`);
      }

      const result = await res.json();
      
      // Start monitoring the job
      const jobRes = await fetch(`${base}/v1/jobs/${result.jobId}`, {
        headers: authHeaders()
      });
      
      if (jobRes.ok) {
        const job = await jobRes.json();
        setActiveJobs(prev => [job, ...prev]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(null);
    }
  }, [base]);

  const handleClientFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0], "clients");
    }
  };

  const handleLoanFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0], "loans");
    }
  };

  const removeJob = (jobId: string) => {
    setActiveJobs(prev => prev.filter(job => job.id !== jobId));
  };

  return (
    <div className="space-y-8">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Upload Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Clients Upload */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Bulk Upload Clients</h2>
          <p className="text-gray-600 mb-4">
            Upload a CSV file with client data. Required columns: displayName. 
            Optional: id, mobile, nationalId, address.
          </p>
          
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv"
                onChange={handleClientFileSelect}
                disabled={uploading === "clients"}
                className="hidden"
                id="clients-upload"
              />
              <label
                htmlFor="clients-upload"
                className={`cursor-pointer ${uploading === "clients" ? "opacity-50" : ""}`}
              >
                {uploading === "clients" ? (
                  <div className="text-blue-600">
                    <div className="mx-auto h-12 w-12 mb-2">⏳</div>
                    <p>Uploading clients...</p>
                  </div>
                ) : (
                  <div>
                    <div className="mx-auto h-12 w-12 text-gray-400 mb-2">📁</div>
                    <p className="text-blue-600 hover:text-blue-800">
                      Click to upload clients CSV
                    </p>
                  </div>
                )}
              </label>
            </div>
            
            <div className="text-xs text-gray-500">
              <strong>Sample CSV format:</strong>
              <pre className="mt-1 bg-gray-50 p-2 rounded">
displayName,mobile,nationalId,address{"\n"}
John Doe,+1234567890,ID123456,123 Main St{"\n"}
Jane Smith,+0987654321,ID789012,456 Oak Ave
              </pre>
            </div>
          </div>
        </div>

        {/* Loans Upload */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Bulk Upload Loans</h2>
          <p className="text-gray-600 mb-4">
            Upload a CSV file with loan data. Required columns: clientId, productId, principal.
            Optional: id, interestRate, termMonths.
          </p>
          
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv"
                onChange={handleLoanFileSelect}
                disabled={uploading === "loans"}
                className="hidden"
                id="loans-upload"
              />
              <label
                htmlFor="loans-upload"
                className={`cursor-pointer ${uploading === "loans" ? "opacity-50" : ""}`}
              >
                {uploading === "loans" ? (
                  <div className="text-blue-600">
                    <div className="mx-auto h-12 w-12 mb-2">⏳</div>
                    <p>Uploading loans...</p>
                  </div>
                ) : (
                  <div>
                    <div className="mx-auto h-12 w-12 text-gray-400 mb-2">📁</div>
                    <p className="text-blue-600 hover:text-blue-800">
                      Click to upload loans CSV
                    </p>
                  </div>
                )}
              </label>
            </div>
            
            <div className="text-xs text-gray-500">
              <strong>Sample CSV format:</strong>
              <pre className="mt-1 bg-gray-50 p-2 rounded">
clientId,productId,principal,interestRate,termMonths{"\n"}
C123,PROD1,10000,12.5,24{"\n"}
C456,PROD2,5000,15.0,12
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Upload Jobs</h2>
          {activeJobs.map((job) => (
            <JobStatusMonitor
              key={job.id}
              jobId={job.id}
              onComplete={() => removeJob(job.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}