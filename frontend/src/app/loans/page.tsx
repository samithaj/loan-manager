"use client";
import { useState } from "react";
import LoansManager from "../../components/LoansManager";

export default function LoansPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Loans</h1>
        <p className="text-gray-600 mt-2">Manage loan applications, approvals, and disbursements</p>
      </div>
      
      <LoansManager />
    </div>
  );
}