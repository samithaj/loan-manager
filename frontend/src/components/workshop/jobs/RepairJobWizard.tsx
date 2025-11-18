"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import BikeSearchSelector from "../common/BikeSearchSelector";
import MechanicSelector from "../common/MechanicSelector";

type JobType =
  | "SERVICE"
  | "ACCIDENT_REPAIR"
  | "FULL_OVERHAUL_BEFORE_SALE"
  | "MAINTENANCE"
  | "CUSTOM_WORK"
  | "WARRANTY_REPAIR";

interface WizardStep1Data {
  bicycleId: number | null;
  jobType: JobType;
  branchId: number | null;
  odometer: number;
  customerComplaint: string;
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
}

interface WizardStep2Data {
  mechanicId: number | null;
  estimatedCompletionDate: string;
  initialDiagnosis: string;
}

export default function RepairJobWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [step1Data, setStep1Data] = useState<WizardStep1Data>({
    bicycleId: null,
    jobType: "SERVICE",
    branchId: null,
    odometer: 0,
    customerComplaint: "",
    priority: "NORMAL",
  });
  const [step2Data, setStep2Data] = useState<WizardStep2Data>({
    mechanicId: null,
    estimatedCompletionDate: "",
    initialDiagnosis: "",
  });
  const [selectedBike, setSelectedBike] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const jobTypeLabels: Record<JobType, string> = {
    SERVICE: "Routine Service",
    ACCIDENT_REPAIR: "Accident Repair",
    FULL_OVERHAUL_BEFORE_SALE: "Full Overhaul Before Sale",
    MAINTENANCE: "Maintenance",
    CUSTOM_WORK: "Custom Work",
    WARRANTY_REPAIR: "Warranty Repair",
  };

  const handleStep1Next = (e: React.FormEvent) => {
    e.preventDefault();
    if (!step1Data.bicycleId) {
      setError("Please select a bike");
      return;
    }
    setError("");
    setCurrentStep(2);
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${base}/v1/workshop/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          bicycle_id: step1Data.bicycleId,
          job_type: step1Data.jobType,
          branch_id: step1Data.branchId,
          odometer: step1Data.odometer,
          customer_complaint: step1Data.customerComplaint,
          priority: step1Data.priority,
          mechanic_id: step2Data.mechanicId,
          estimated_completion_date: step2Data.estimatedCompletionDate || null,
          diagnosis: step2Data.initialDiagnosis,
        }),
      });

      if (res.ok) {
        const job = await res.json();
        router.push(`/workshop/jobs/${job.id}`);
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to create job");
      }
    } catch (err) {
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-center gap-4">
          <div className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                currentStep >= 1 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
              }`}
            >
              1
            </div>
            <span className="ml-2 font-medium text-gray-700">Basic Info</span>
          </div>
          <div className="w-16 h-1 bg-gray-200">
            <div
              className={`h-full transition-all ${currentStep >= 2 ? "bg-blue-600" : ""}`}
              style={{ width: currentStep >= 2 ? "100%" : "0%" }}
            />
          </div>
          <div className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                currentStep >= 2 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
              }`}
            >
              2
            </div>
            <span className="ml-2 font-medium text-gray-700">Assignment</span>
          </div>
          <div className="w-16 h-1 bg-gray-200">
            <div
              className={`h-full transition-all ${currentStep >= 3 ? "bg-blue-600" : ""}`}
              style={{ width: currentStep >= 3 ? "100%" : "0%" }}
            />
          </div>
          <div className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                currentStep >= 3 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
              }`}
            >
              3
            </div>
            <span className="ml-2 font-medium text-gray-700">Review</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        )}

        {/* Step 1: Basic Info */}
        {currentStep === 1 && (
          <form onSubmit={handleStep1Next} className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Basic Job Information</h2>

            <BikeSearchSelector
              onSelect={(bike) => {
                setSelectedBike(bike);
                setStep1Data({
                  ...step1Data,
                  bicycleId: bike.id,
                  branchId: bike.branch_id || null,
                  odometer: bike.odometer || 0,
                });
              }}
              label="Select Bike"
              placeholder="Search by license plate or frame number..."
              required
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Type <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={step1Data.jobType}
                  onChange={(e) =>
                    setStep1Data({ ...step1Data, jobType: e.target.value as JobType })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.entries(jobTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={step1Data.priority}
                  onChange={(e) =>
                    setStep1Data({
                      ...step1Data,
                      priority: e.target.value as WizardStep1Data["priority"],
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Odometer (km)
              </label>
              <input
                type="number"
                min="0"
                value={step1Data.odometer || ""}
                onChange={(e) =>
                  setStep1Data({ ...step1Data, odometer: parseInt(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Customer Complaint / Reason for Service
              </label>
              <textarea
                value={step1Data.customerComplaint}
                onChange={(e) =>
                  setStep1Data({ ...step1Data, customerComplaint: e.target.value })
                }
                rows={4}
                placeholder="Describe the issue or service request..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Next →
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Assignment */}
        {currentStep === 2 && (
          <form onSubmit={(e) => { e.preventDefault(); setCurrentStep(3); }} className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Assignment Details</h2>

            <MechanicSelector
              value={step2Data.mechanicId}
              onChange={(mechanicId) => setStep2Data({ ...step2Data, mechanicId })}
              label="Assign Mechanic"
              branchId={step1Data.branchId || undefined}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Completion Date
              </label>
              <input
                type="date"
                value={step2Data.estimatedCompletionDate}
                onChange={(e) =>
                  setStep2Data({ ...step2Data, estimatedCompletionDate: e.target.value })
                }
                min={new Date().toISOString().split("T")[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Initial Diagnosis (Optional)
              </label>
              <textarea
                value={step2Data.initialDiagnosis}
                onChange={(e) => setStep2Data({ ...step2Data, initialDiagnosis: e.target.value })}
                rows={4}
                placeholder="Initial assessment or diagnosis..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex justify-between gap-3 pt-6 border-t">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ← Back
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Next →
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Review */}
        {currentStep === 3 && (
          <form onSubmit={handleCreateJob} className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Review & Create Job</h2>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Bike Information</h3>
                {selectedBike && (
                  <div className="text-sm text-gray-700 space-y-1">
                    <p>
                      <strong>Model:</strong> {selectedBike.title || `${selectedBike.make} ${selectedBike.model}`}
                    </p>
                    <p>
                      <strong>License:</strong> {selectedBike.license_plate}
                    </p>
                    <p>
                      <strong>Frame:</strong> {selectedBike.frame_number}
                    </p>
                  </div>
                )}
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Job Details</h3>
                <div className="text-sm text-gray-700 space-y-1">
                  <p>
                    <strong>Type:</strong> {jobTypeLabels[step1Data.jobType]}
                  </p>
                  <p>
                    <strong>Priority:</strong> {step1Data.priority}
                  </p>
                  <p>
                    <strong>Odometer:</strong> {step1Data.odometer.toLocaleString()} km
                  </p>
                  {step1Data.customerComplaint && (
                    <p>
                      <strong>Complaint:</strong> {step1Data.customerComplaint}
                    </p>
                  )}
                </div>
              </div>

              {(step2Data.mechanicId || step2Data.estimatedCompletionDate) && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Assignment</h3>
                  <div className="text-sm text-gray-700 space-y-1">
                    {step2Data.mechanicId && (
                      <p>
                        <strong>Mechanic:</strong> Assigned
                      </p>
                    )}
                    {step2Data.estimatedCompletionDate && (
                      <p>
                        <strong>Est. Completion:</strong> {step2Data.estimatedCompletionDate}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-between gap-3 pt-6 border-t">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                disabled={loading}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:bg-gray-200"
              >
                ← Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
              >
                {loading ? "Creating..." : "Create Job"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
