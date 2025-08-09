import ClientsManager from '@/components/ClientsManager';

export default function ClientsPage() {
  return (
    <main className="min-h-screen p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Clients</h1>
      <ClientsManager />
    </main>
  );
}


