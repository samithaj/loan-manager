"use client";
import { useState } from "react";

export default function LoanActions({ loanId, status, onChanged }: { loanId: string; status: string; onChanged?: () => void }) {
  const [loading, setLoading] = useState<string | null>(null);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  async function run(command: "approve" | "disburse" | "close") {
    setLoading(command);
    try {
      const res = await fetch(`${base}/v1/loans/${loanId}?command=${command}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
      });
      if (res.ok) {
        onChanged?.();
      } else {
        console.error("command failed", await res.text());
        alert("Action failed");
      }
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="flex gap-2">
      <button
        className="px-3 py-1 rounded border disabled:opacity-50"
        disabled={status !== "PENDING" || loading !== null}
        onClick={() => run("approve")}
      >
        {loading === "approve" ? "Approving…" : "Approve"}
      </button>
      <button
        className="px-3 py-1 rounded border disabled:opacity-50"
        disabled={status !== "APPROVED" || loading !== null}
        onClick={() => run("disburse")}
      >
        {loading === "disburse" ? "Disbursing…" : "Disburse"}
      </button>
      <button
        className="px-3 py-1 rounded border disabled:opacity-50"
        disabled={!(status === "DISBURSED") || loading !== null}
        onClick={() => run("close")}
      >
        {loading === "close" ? "Closing…" : "Close"}
      </button>
    </div>
  );
}



