"use client";
import { useState } from "react";

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function ReportsManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function downloadReport(reportType: "loan-portfolio" | "delinquency", format: "JSON" | "CSV", params: Record<string, string> = {}) {
    setLoading(`${reportType}-${format}`);
    setError(null);

    try {
      const url = new URL(`${base}/v1/reports/${reportType}/run`);
      url.searchParams.set("format", format);
      
      Object.entries(params).forEach(([key, value]) => {
        if (value) url.searchParams.set(key, value);
      });

      const res = await fetch(url.toString(), {
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      if (format === "CSV") {
        // Download CSV file
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${reportType}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
      } else {
        // Show JSON in new tab
        const data = await res.json();
        const jsonWindow = window.open();
        if (jsonWindow) {
          jsonWindow.document.write(`<pre>${JSON.stringify(data, null, 2)}</pre>`);
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(null);
    }
  }

  async function runDelinquencyClassification() {
    setLoading("delinquency-job");
    setError(null);

    try {
      const res = await fetch(`${base}/v1/jobs/delinquency-classification`, {
        method: "POST",
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      const result = await res.json();
      alert(`Delinquency classification completed. Processed ${result.processedLoans} loans.`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Loan Portfolio Report */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Loan Portfolio Report</h2>
        <p className="text-gray-600 mb-6">
          Generate a comprehensive report of all loans in the system.
        </p>
        
        <div className="flex gap-4">
          <button
            onClick={() => downloadReport("loan-portfolio", "JSON")}
            disabled={loading === "loan-portfolio-JSON"}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading === "loan-portfolio-JSON" ? "Generating..." : "View JSON"}
          </button>
          <button
            onClick={() => downloadReport("loan-portfolio", "CSV")}
            disabled={loading === "loan-portfolio-CSV"}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
          >
            {loading === "loan-portfolio-CSV" ? "Generating..." : "Download CSV"}
          </button>
        </div>
      </div>

      {/* Delinquency Report */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Delinquency Report</h2>
        <p className="text-gray-600 mb-6">
          Generate a report showing current delinquency status of all loans.
        </p>
        
        <div className="space-y-4">
          <div className="flex gap-4">
            <button
              onClick={() => downloadReport("delinquency", "JSON")}
              disabled={loading === "delinquency-JSON"}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading === "delinquency-JSON" ? "Generating..." : "View JSON"}
            </button>
            <button
              onClick={() => downloadReport("delinquency", "CSV")}
              disabled={loading === "delinquency-CSV"}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              {loading === "delinquency-CSV" ? "Generating..." : "Download CSV"}
            </button>
          </div>
          
          <div className="border-t pt-4">
            <button
              onClick={runDelinquencyClassification}
              disabled={loading === "delinquency-job"}
              className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:bg-gray-400"
            >
              {loading === "delinquency-job" ? "Running..." : "Run Delinquency Classification"}
            </button>
            <p className="text-xs text-gray-500 mt-1">
              Updates delinquency buckets for all disbursed loans
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Report Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-50 p-4 rounded">
            <h4 className="font-medium mb-2">Loan Portfolio CSV Columns:</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Loan ID, Client ID, Product ID</li>
              <li>• Principal, Interest Rate, Term</li>
              <li>• Status, Disbursed Date, Created Date</li>
            </ul>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <h4 className="font-medium mb-2">Delinquency CSV Columns:</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Loan ID, Client ID, Client Name</li>
              <li>• Principal, Loan Status</li>
              <li>• Bucket ID, Bucket Name, Days Past Due</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}