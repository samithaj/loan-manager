"use client";
import BulkUploadManager from "../../components/BulkUploadManager";

export default function BulkUploadPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Bulk Upload</h1>
        <p className="text-gray-600 mt-2">Upload CSV files to create multiple clients or loans</p>
      </div>
      
      <BulkUploadManager />
    </div>
  );
}