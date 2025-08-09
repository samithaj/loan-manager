"use client";
import { useEffect, useState } from 'react';

type Me = { username: string; roles: string[] } | null;

export default function ProfilePage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const [me, setMe] = useState<Me>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`${base}/v1/me`, { credentials: 'include', cache: 'no-store' });
        if (res.ok) {
          const data = (await res.json()) as { username: string; roles: string[] };
          if (!cancelled) setMe(data);
        } else {
          if (!cancelled) setMe(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [base]);

  return (
    <main className="min-h-screen space-y-4">
      <h1 className="text-2xl font-semibold">Profile</h1>
      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : me ? (
        <div className="space-y-2 text-sm">
          <div><span className="text-gray-500">Username:</span> {me.username}</div>
          <div><span className="text-gray-500">Roles:</span> {me.roles?.join(', ') || '—'}</div>
          <div className="text-gray-500">Permissions:</div>
          <ul className="list-disc pl-6 text-gray-300">
            {(me.roles || []).map((r) => (
              <li key={r}>role:{r}</li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="text-sm text-red-600">Not signed in. Please login.</div>
      )}
    </main>
  );
}


