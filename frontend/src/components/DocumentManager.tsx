"use client";
import { useEffect, useState } from "react";
import DocumentUploader from "./DocumentUploader";

type Document = {
  id: string;
  ownerType: string;
  ownerId: string;
  name: string;
  mimeType: string;
  size: number;
  uploadedOn: string;
};

interface DocumentManagerProps {
  ownerType: "CLIENT" | "LOAN";
  ownerId: string;
  title?: string;
}

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function DocumentManager({ ownerType, ownerId, title }: DocumentManagerProps) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments() {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${base}/v1/documents`);
      url.searchParams.set("ownerType", ownerType);
      url.searchParams.set("ownerId", ownerId);

      const res = await fetch(url.toString(), {
        cache: "no-store",
        headers: authHeaders()
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = (await res.json()) as Document[];
      setDocuments(data);
    } catch {
      setError("Failed to load documents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ownerType, ownerId]);

  async function onDelete(documentId: string) {
    if (!confirm("Are you sure you want to delete this document?")) return;
    
    setError(null);
    try {
      const res = await fetch(`${base}/v1/documents/${documentId}`, {
        method: "DELETE",
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      await loadDocuments();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function downloadDocument(documentId: string, filename: string) {
    const link = document.createElement('a');
    link.href = `${base}/v1/documents/${documentId}`;
    link.download = filename;
    link.target = '_blank';
    
    // Add auth headers for download (simplified approach)
    const authHeader = authHeaders().Authorization;
    if (authHeader) {
      // For downloads, we'll open in new tab and let browser handle auth
      window.open(`${base}/v1/documents/${documentId}`, '_blank');
    } else {
      link.click();
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith("image/")) {
      return "🖼️";
    } else if (mimeType === "application/pdf") {
      return "📄";
    } else if (mimeType.includes("word")) {
      return "📝";
    } else if (mimeType.includes("excel") || mimeType.includes("sheet")) {
      return "📊";
    } else {
      return "📎";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">{title || "Documents"}</h3>
      </div>

      {/* Upload Area */}
      <DocumentUploader
        ownerType={ownerType}
        ownerId={ownerId}
        onUploadComplete={() => loadDocuments()}
      />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Document List */}
      {loading ? (
        <div className="text-center py-4">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No documents uploaded</div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <h4 className="text-sm font-medium text-gray-700">Uploaded Documents</h4>
          </div>
          <div className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <div key={doc.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getFileIcon(doc.mimeType)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(doc.size)} • {new Date(doc.uploadedOn).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => downloadDocument(doc.id, doc.name)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => onDelete(doc.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}