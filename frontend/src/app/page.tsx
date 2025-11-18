import Link from 'next/link';
import ApplicationPipelineWidget from '@/components/ApplicationPipelineWidget';
import InventoryStatusWidget from '@/components/InventoryStatusWidget';
import BranchPerformanceWidget from '@/components/BranchPerformanceWidget';

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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Loan Manager Dashboard</h1>
        <div className="text-sm text-gray-600">Health: {health?.status ?? 'unknown'}</div>
      </div>

      {!me ? (
        <div className="space-y-2">
          <p className="text-sm text-gray-500">You are not signed in.</p>
          <Link className="underline text-blue-600" href="/login">Go to Login</Link>
        </div>
      ) : (
        <>
          {/* Dashboard Widgets */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <ApplicationPipelineWidget />
            <InventoryStatusWidget />
            <BranchPerformanceWidget />
          </div>

          {/* Quick Links */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <Link
                href="/applications"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Applications</div>
                <div className="text-xs text-gray-500">Manage bicycle applications</div>
              </Link>
              <Link
                href="/inventory"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Inventory</div>
                <div className="text-xs text-gray-500">Manage bicycle stock</div>
              </Link>
              <Link
                href="/clients"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Clients</div>
                <div className="text-xs text-gray-500">View all clients</div>
              </Link>
              <Link
                href="/loan-products"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Loan Products</div>
                <div className="text-xs text-gray-500">Manage loan products</div>
              </Link>
              <Link
                href="/reference"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Reference Data</div>
                <div className="text-xs text-gray-500">View reference data</div>
              </Link>
              <Link
                href="/reference/offices"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Offices</div>
                <div className="text-xs text-gray-500">Manage branches</div>
              </Link>
              <Link
                href="/reference/staff"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Staff</div>
                <div className="text-xs text-gray-500">Manage staff users</div>
              </Link>
              <Link
                href="/bicycles"
                className="p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-gray-900">Public Site</div>
                <div className="text-xs text-gray-500">View public bicycle site</div>
              </Link>
            </div>
          </div>
        </>
      )}
    </main>
  );
}
