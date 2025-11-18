"use client";
import { useState } from 'react';

export default function QuickDisburse({ clientId }: { clientId: string }) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const [loanId, setLoanId] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  async function run(command: 'approve' | 'disburse') {
    if (!loanId) return;
    setBusy(command);
    try {
      const res = await fetch(`${base}/v1/loans/${loanId}?command=${command}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
      });
      if (!res.ok) alert(`Failed to ${command} (${res.status})`);
    } finally {
      setBusy(null);
    }
  }
  return (
    <section className="mt-6 space-y-2">
      <h2 className="text-lg font-semibold">Quick loan actions</h2>
      <div className="text-xs text-gray-500">Approve or disburse an existing loan for this client.</div>
      <div className="flex gap-2 items-end">
        <div className="flex flex-col">
          <label className="text-xs">Loan ID</label>
          <input className="border rounded px-2 py-1 bg-transparent" value={loanId} onChange={(e) => setLoanId(e.target.value)} placeholder="LN-..." />
        </div>
        <button className="border rounded px-3 py-1 disabled:opacity-50" disabled={!loanId || !!busy} onClick={() => run('approve')}>{busy==='approve'?'Approving…':'Approve'}</button>
        <button className="border rounded px-3 py-1 disabled:opacity-50" disabled={!loanId || !!busy} onClick={() => run('disburse')}>{busy==='disburse'?'Disbursing…':'Disburse'}</button>
      </div>
    </section>
  );
}



