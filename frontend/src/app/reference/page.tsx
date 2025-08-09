import Link from 'next/link';

export default function ReferencePage() {
  return (
    <main className="min-h-screen p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Reference Data</h1>
      <p className="text-sm text-gray-600">Manage organization reference data in dedicated pages.</p>

      <ul className="list-disc pl-6 space-y-2 text-blue-700">
        <li>
          <Link className="underline" href="/reference/offices">Offices</Link>
        </li>
        <li>
          <Link className="underline" href="/reference/staff">Staff</Link>
        </li>
        <li>
          <Link className="underline" href="/reference/holidays">Holidays</Link>
        </li>
        <li>
          <Link className="underline" href="/loan-products">Loan products</Link>
        </li>
      </ul>
    </main>
  );
}

