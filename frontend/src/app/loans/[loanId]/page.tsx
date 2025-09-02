"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import LoanWorkspace from "../../../components/LoanWorkspace";

export default function LoanDetailPage() {
  const params = useParams();
  const loanId = params.loanId as string;

  return (
    <div className="min-h-screen bg-gray-50">
      <LoanWorkspace loanId={loanId} />
    </div>
  );
}