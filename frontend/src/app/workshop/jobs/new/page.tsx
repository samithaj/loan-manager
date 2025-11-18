"use client";
import RepairJobWizard from "@/components/workshop/jobs/RepairJobWizard";

export default function NewRepairJobPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Create New Repair Job</h1>
        <p className="text-gray-600 mt-1">
          Fill in the details below to create a new repair job
        </p>
      </div>

      <RepairJobWizard />
    </div>
  );
}
