"use client";
import { useState } from 'react';

export default function ReferenceActions() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function seedHoliday() {
    setBusy(true); setMsg(null);
    const id = `H${Date.now()}`;
    const today = new Date().toISOString().slice(0,10);
    const res = await fetch(`${base}/v1/holidays`, {
      method: 'POST',
      headers: {
        'Content-Type':'application/json',
        // include basic auth if present in localStorage
        ...(typeof window !== 'undefined' && localStorage.getItem('u') && localStorage.getItem('p')
          ? { Authorization: 'Basic ' + btoa(`${localStorage.getItem('u')}:${localStorage.getItem('p')}`) }
          : {}),
      },
      body: JSON.stringify({ id, name: 'Demo Holiday', date: today })
    });
    setBusy(false);
    setMsg(res.ok ? 'Added a holiday. Refresh the page.' : 'Failed to add.');
  }

  return (
    <div className="text-sm flex items-center gap-3">
      <button className="border rounded px-3 py-1" disabled={busy} onClick={seedHoliday}>Add holiday (demo)</button>
      {msg && <span className="text-gray-500">{msg}</span>}
    </div>
  );
}


