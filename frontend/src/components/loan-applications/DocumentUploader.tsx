"use client";

import { useState } from "react";

interface DocumentUploaderProps {
  applicationId: string;
  onUploadComplete?: () => void;
}

const DOCUMENT_TYPES = [
  { value: "NIC_FRONT", label: "NIC Front" },
  { value: "NIC_BACK", label: "NIC Back" },
  { value: "CUSTOMER_PHOTO", label: "Customer Photo" },
  { value: "CUSTOMER_SELFIE", label: "Customer Selfie" },
  { value: "PROOF_OF_ADDRESS", label: "Proof of Address" },
  { value: "CERTIFICATE_OF_REGISTRATION", label: "Certificate of Registration" },
  { value: "VEHICLE_PHOTO_FRONT", label: "Vehicle Photo - Front" },
  { value: "VEHICLE_PHOTO_BACK", label: "Vehicle Photo - Back" },
  { value: "VEHICLE_PHOTO_SIDE", label: "Vehicle Photo - Side" },
  { value: "VEHICLE_PHOTO_DASHBOARD", label: "Vehicle Photo - Dashboard" },
  { value: "VEHICLE_PHOTO_ENGINE", label: "Vehicle Photo - Engine" },
  { value: "BANK_STATEMENT", label: "Bank Statement" },
  { value: "SALARY_SLIP", label: "Salary Slip" },
  { value: "OTHER", label: "Other" },
];

export default function DocumentUploader({ applicationId, onUploadComplete }: DocumentUploaderProps) {
  const [docType, setDocType] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !docType) {
      alert("Please select document type and file");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Step 1: Get pre-signed URL
      const presignResponse = await fetch(
        `/api/v1/loan-applications/${applicationId}/documents/presign`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            doc_type: docType,
            filename: file.name,
            content_type: file.type,
            file_size: file.size,
          }),
        }
      );

      if (!presignResponse.ok) {
        throw new Error("Failed to get upload URL");
      }

      const { upload_url, file_url, doc_id } = await presignResponse.json();

      // Step 2: Upload file to storage
      setUploadProgress(30);

      // For local storage, we'll upload via our API
      // For S3, we would upload directly to the presigned URL
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": file.type,
        },
      });

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload file");
      }

      setUploadProgress(70);

      // Step 3: Confirm upload
      const confirmResponse = await fetch(
        `/api/v1/loan-applications/documents/${doc_id}/confirm`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            doc_id,
            meta_json: {
              uploaded_from: "web",
            },
          }),
        }
      );

      if (!confirmResponse.ok) {
        throw new Error("Failed to confirm upload");
      }

      setUploadProgress(100);

      // Reset form
      setFile(null);
      setDocType("");
      if (onUploadComplete) {
        onUploadComplete();
      }

      alert("Document uploaded successfully!");
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload document");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Upload Document</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Document Type*</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full px-4 py-2 border rounded"
            disabled={uploading}
          >
            <option value="">Select Document Type</option>
            {DOCUMENT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">File*</label>
          <input
            type="file"
            onChange={handleFileChange}
            accept="image/*,.pdf"
            className="w-full px-4 py-2 border rounded"
            disabled={uploading}
          />
          {file && (
            <div className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {uploading && (
          <div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Uploading... {uploadProgress}%
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || !docType || uploading}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? "Uploading..." : "Upload Document"}
        </button>
      </div>
    </div>
  );
}
