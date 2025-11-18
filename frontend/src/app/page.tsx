import Link from 'next/link';

async function fetchMe() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${base}/v1/me`, { cache: 'no-store', credentials: 'include' });
    if (!res.ok) return null;
    return (await res.json()) as { username: string; roles: string[] };
  } catch { return null; }
}

export default async function Home() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const [health, me] = await Promise.all([
    fetch(`${base}/v1/health`, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    fetchMe(),
  ]);

  return (
    <main className="min-h-screen space-y-6">
      <h1 className="text-2xl font-semibold">Loan Manager</h1>
      <div className="text-sm text-gray-600">Health: {health?.status ?? 'unknown'}</div>
      {!me ? (
        <div className="space-y-2">
          <p className="text-sm text-gray-500">You are not signed in.</p>
          <Link className="underline text-blue-600" href="/login">Go to Login</Link>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-gray-500">Quick links:</p>
          <ul className="list-disc pl-6 text-blue-700 space-y-1">
            <li><Link className="underline" href="/reference">Reference data</Link></li>
            <li><Link className="underline" href="/reference/offices">Offices</Link></li>
            <li><Link className="underline" href="/reference/staff">Staff</Link></li>
            <li><Link className="underline" href="/reference/holidays">Holidays</Link></li>
            <li><Link className="underline" href="/loan-products">Loan products</Link></li>
            <li><Link className="underline" href="/clients">Clients</Link></li>
            <li><Link className="underline" href="/loans">Loans</Link></li>
          </ul>
        </div>
      )}
    </main>
  );
}
