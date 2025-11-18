"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface LeaveType {
  id: string;
  name: string;
  description?: string;
  default_days_per_year: number;
  requires_approval: boolean;
  requires_documentation: boolean;
  max_consecutive_days?: number;
  is_paid: boolean;
}

export default function ApplyLeavePage() {
  const router = useRouter();
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    leave_type_id: "",
    start_date: "",
    end_date: "",
    total_days: 0,
    reason: "",
    document_url: ""
  });

  useEffect(() => {
    fetchLeaveTypes();
  }, []);

  useEffect(() => {
    // Calculate total days when dates change
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const diffTime = Math.abs(end.getTime() - start.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      setFormData({ ...formData, total_days: diffDays });
    }
  }, [formData.start_date, formData.end_date]);

  const fetchLeaveTypes = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave/types`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setLeaveTypes(data);
      }
    } catch (error) {
      console.error("Error fetching leave types:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.leave_type_id) {
      alert("Please select a leave type");
      return;
    }

    if (!formData.start_date || !formData.end_date) {
      alert("Please select start and end dates");
      return;
    }

    if (formData.start_date > formData.end_date) {
      alert("End date must be after or equal to start date");
      return;
    }

    if (!formData.reason || formData.reason.length < 10) {
      alert("Please provide a reason (at least 10 characters)");
      return;
    }

    const selectedType = leaveTypes.find((lt) => lt.id === formData.leave_type_id);
    if (selectedType?.requires_documentation && !formData.document_url) {
      alert("This leave type requires documentation");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/leave/applications`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData)
        }
      );

      if (response.ok) {
        alert("Leave application submitted successfully!");
        router.push("/hr/leaves");
      } else {
        const error = await response.json();
        alert(`Failed to submit: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error submitting leave application:", error);
      alert("An error occurred while submitting the application");
    } finally {
      setLoading(false);
    }
  };

  const selectedType = leaveTypes.find((lt) => lt.id === formData.leave_type_id);

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Apply for Leave</h1>
        <p className="mt-2 text-gray-600">
          Submit a new leave application for approval
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Leave Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Leave Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.leave_type_id}
              onChange={(e) =>
                setFormData({ ...formData, leave_type_id: e.target.value })
              }
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select leave type</option>
              {leaveTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name} {type.is_paid ? "(Paid)" : "(Unpaid)"}
                  {type.max_consecutive_days &&
                    ` - Max ${type.max_consecutive_days} days`}
                </option>
              ))}
            </select>
            {selectedType?.description && (
              <p className="mt-1 text-sm text-gray-500">
                {selectedType.description}
              </p>
            )}
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) =>
                  setFormData({ ...formData, start_date: e.target.value })
                }
                required
                min={new Date().toISOString().split("T")[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) =>
                  setFormData({ ...formData, end_date: e.target.value })
                }
                required
                min={formData.start_date || new Date().toISOString().split("T")[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Total Days (calculated) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Total Days
            </label>
            <input
              type="number"
              value={formData.total_days}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  total_days: parseFloat(e.target.value)
                })
              }
              step="0.5"
              min="0.5"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              Automatically calculated. You can adjust for half-days.
            </p>
          </div>

          {/* Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.reason}
              onChange={(e) =>
                setFormData({ ...formData, reason: e.target.value })
              }
              required
              minLength={10}
              rows={4}
              placeholder="Please provide a detailed reason for your leave application (minimum 10 characters)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              {formData.reason.length}/1000 characters
            </p>
          </div>

          {/* Documentation URL (if required) */}
          {selectedType?.requires_documentation && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Documentation URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={formData.document_url}
                onChange={(e) =>
                  setFormData({ ...formData, document_url: e.target.value })
                }
                required
                placeholder="https://example.com/document.pdf"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-sm text-gray-500">
                This leave type requires supporting documentation
              </p>
            </div>
          )}

          {/* Warnings */}
          {selectedType && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">
                Leave Type Information
              </h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>
                  • Type: {selectedType.is_paid ? "Paid" : "Unpaid"} leave
                </li>
                {selectedType.requires_approval && (
                  <li>• Requires manager approval</li>
                )}
                {selectedType.max_consecutive_days && (
                  <li>
                    • Maximum consecutive days: {selectedType.max_consecutive_days}
                  </li>
                )}
                {selectedType.requires_documentation && (
                  <li>• Supporting documentation required</li>
                )}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {loading ? "Submitting..." : "Submit Application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
