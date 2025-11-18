type Client = { id: string; displayName: string; mobile?: string | null; nationalId?: string | null; address?: string | null };

async function fetchClient(clientId: string): Promise<Client | null> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${base}/v1/clients/${clientId}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return (await res.json()) as Client;
  } catch {
    return null;
  }
}

export default async function ClientPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = await params;
  const client = await fetchClient(clientId);
  return (
    <main className="min-h-screen p-8 space-y-4">
      <h1 className="text-2xl font-semibold">Client {clientId}</h1>
      {!client ? (
        <div className="text-sm text-red-600">Not found</div>
      ) : (
        <div className="text-sm space-y-1">
          <div><span className="font-medium">Name:</span> {client.displayName}</div>
          <div><span className="font-medium">Mobile:</span> {client.mobile || '-'}</div>
          <div><span className="font-medium">NIC:</span> {client.nationalId || '-'}</div>
          <div><span className="font-medium">Address:</span> {client.address || '-'}</div>
        </div>
      )}
      <QuickDisburse clientId={clientId} />
    </main>
  );
}

// Client component is split to a separate file to avoid mixing server/client directives
import QuickDisburse from './quick-disburse';

