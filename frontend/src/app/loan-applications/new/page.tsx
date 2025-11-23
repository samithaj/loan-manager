"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Branch {
  id: string;
  code: string;
  name: string;
}

interface FormData {
  branch_id: string;
  requested_amount: string;
  tenure_months: string;
  lmo_notes: string;
  customer: {
    nic: string;
    full_name: string;
    dob: string;
    address: string;
    phone: string;
    email: string;
  };
  vehicle: {
    chassis_no: string;
    engine_no: string;
    make: string;
    model: string;
    year: string;
    color: string;
    registration_no: string;
  };
}

export default function NewLoanApplicationPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    branch_id: "",
    requested_amount: "",
    tenure_months: "36",
    lmo_notes: "",
    customer: {
      nic: "",
      full_name: "",
      dob: "",
      address: "",
      phone: "",
      email: "",
    },
    vehicle: {
      chassis_no: "",
      engine_no: "",
      make: "",
      model: "",
      year: "",
      color: "",
      registration_no: "",
    },
  });

  useEffect(() => {
    fetchBranches();
  }, []);

  const fetchBranches = async () => {
    try {
      const response = await fetch("/api/v1/loan-applications/branches", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setBranches(data);
      }
    } catch (error) {
      console.error("Failed to fetch branches:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent, asDraft: boolean = false) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create application
      const payload = {
        ...formData,
        requested_amount: parseFloat(formData.requested_amount),
        tenure_months: parseInt(formData.tenure_months),
        customer: {
          ...formData.customer,
          dob: formData.customer.dob || null,
        },
        vehicle: {
          ...formData.vehicle,
          year: formData.vehicle.year ? parseInt(formData.vehicle.year) : null,
        },
      };

      const response = await fetch("/api/v1/loan-applications", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const application = await response.json();

        // If not draft, submit immediately
        if (!asDraft) {
          await fetch(`/api/v1/loan-applications/${application.id}/submit`, {
            method: "POST",
            credentials: "include",
          });
        }

        router.push(`/loan-applications/${application.id}`);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error("Failed to create application:", error);
      alert("Failed to create application");
    } finally {
      setLoading(false);
    }
  };

  const updateFormData = (section: keyof FormData, field: string, value: string) => {
    if (section === "customer" || section === "vehicle") {
      setFormData((prev) => ({
        ...prev,
        [section]: {
          ...(prev[section] as object),
          [field]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">New Loan Application</h1>

      {/* Progress Steps */}
      <div className="flex justify-between mb-8">
        {[1, 2, 3, 4].map((s) => (
          <div
            key={s}
            className={`flex-1 text-center ${
              s <= step ? "text-blue-600" : "text-gray-400"
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                s <= step ? "bg-blue-600 text-white" : "bg-gray-300"
              }`}
            >
              {s}
            </div>
            <div className="text-sm">
              {s === 1 && "Loan Details"}
              {s === 2 && "Customer Info"}
              {s === 3 && "Vehicle Info"}
              {s === 4 && "Review"}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={(e) => handleSubmit(e, false)} className="bg-white rounded-lg shadow p-6">
        {/* Step 1: Loan Details */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Loan Details</h2>

            <div>
              <label className="block text-sm font-medium mb-2">Branch*</label>
              <select
                required
                value={formData.branch_id}
                onChange={(e) => updateFormData("branch_id" as any, "branch_id", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              >
                <option value="">Select Branch</option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name} ({branch.code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Requested Amount (Rs.)*
              </label>
              <input
                type="number"
                required
                min="1"
                step="0.01"
                value={formData.requested_amount}
                onChange={(e) => updateFormData("requested_amount" as any, "requested_amount", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Tenure (Months)*
              </label>
              <select
                required
                value={formData.tenure_months}
                onChange={(e) => updateFormData("tenure_months" as any, "tenure_months", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              >
                {[12, 24, 36, 48, 60, 72, 84, 96].map((months) => (
                  <option key={months} value={months}>
                    {months} months ({(months / 12).toFixed(1)} years)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Notes</label>
              <textarea
                rows={4}
                value={formData.lmo_notes}
                onChange={(e) => updateFormData("lmo_notes" as any, "lmo_notes", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>
          </div>
        )}

        {/* Step 2: Customer Info */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Customer Information</h2>

            <div>
              <label className="block text-sm font-medium mb-2">NIC Number*</label>
              <input
                type="text"
                required
                value={formData.customer.nic}
                onChange={(e) => updateFormData("customer", "nic", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Full Name*</label>
              <input
                type="text"
                required
                value={formData.customer.full_name}
                onChange={(e) => updateFormData("customer", "full_name", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Date of Birth</label>
              <input
                type="date"
                value={formData.customer.dob}
                onChange={(e) => updateFormData("customer", "dob", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Address*</label>
              <textarea
                required
                rows={3}
                value={formData.customer.address}
                onChange={(e) => updateFormData("customer", "address", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Phone*</label>
              <input
                type="tel"
                required
                value={formData.customer.phone}
                onChange={(e) => updateFormData("customer", "phone", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <input
                type="email"
                value={formData.customer.email}
                onChange={(e) => updateFormData("customer", "email", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>
          </div>
        )}

        {/* Step 3: Vehicle Info */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Vehicle Information</h2>

            <div>
              <label className="block text-sm font-medium mb-2">Chassis Number*</label>
              <input
                type="text"
                required
                value={formData.vehicle.chassis_no}
                onChange={(e) => updateFormData("vehicle", "chassis_no", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Engine Number</label>
              <input
                type="text"
                value={formData.vehicle.engine_no}
                onChange={(e) => updateFormData("vehicle", "engine_no", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Make*</label>
                <input
                  type="text"
                  required
                  value={formData.vehicle.make}
                  onChange={(e) => updateFormData("vehicle", "make", e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Model*</label>
                <input
                  type="text"
                  required
                  value={formData.vehicle.model}
                  onChange={(e) => updateFormData("vehicle", "model", e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Year</label>
                <input
                  type="number"
                  min="1900"
                  max={new Date().getFullYear() + 1}
                  value={formData.vehicle.year}
                  onChange={(e) => updateFormData("vehicle", "year", e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Color</label>
                <input
                  type="text"
                  value={formData.vehicle.color}
                  onChange={(e) => updateFormData("vehicle", "color", e.target.value)}
                  className="w-full px-4 py-2 border rounded"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Registration Number</label>
              <input
                type="text"
                value={formData.vehicle.registration_no}
                onChange={(e) => updateFormData("vehicle", "registration_no", e.target.value)}
                className="w-full px-4 py-2 border rounded"
              />
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold mb-4">Review & Submit</h2>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Loan Details</h3>
                <dl className="space-y-1 text-sm">
                  <dt className="text-gray-600">Amount:</dt>
                  <dd>Rs. {parseFloat(formData.requested_amount).toLocaleString()}</dd>
                  <dt className="text-gray-600">Tenure:</dt>
                  <dd>{formData.tenure_months} months</dd>
                </dl>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Customer</h3>
                <dl className="space-y-1 text-sm">
                  <dt className="text-gray-600">Name:</dt>
                  <dd>{formData.customer.full_name}</dd>
                  <dt className="text-gray-600">NIC:</dt>
                  <dd>{formData.customer.nic}</dd>
                  <dt className="text-gray-600">Phone:</dt>
                  <dd>{formData.customer.phone}</dd>
                </dl>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Vehicle</h3>
                <dl className="space-y-1 text-sm">
                  <dt className="text-gray-600">Make/Model:</dt>
                  <dd>{formData.vehicle.make} {formData.vehicle.model}</dd>
                  <dt className="text-gray-600">Chassis No:</dt>
                  <dd>{formData.vehicle.chassis_no}</dd>
                </dl>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="px-6 py-2 border rounded hover:bg-gray-50"
              >
                Previous
              </button>
            )}
          </div>

          <div className="flex gap-2">
            {step < 4 && (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Next
              </button>
            )}

            {step === 4 && (
              <>
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e as any, true)}
                  disabled={loading}
                  className="px-6 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Save as Draft
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Submitting..." : "Submit Application"}
                </button>
              </>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
