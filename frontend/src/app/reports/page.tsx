"use client";
import ReportsManager from "../../components/ReportsManager";

export default function ReportsPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
        <p className="text-gray-600 mt-2">Generate and download loan portfolio and delinquency reports</p>
      </div>
      
      <ReportsManager />
    </div>
  );
}