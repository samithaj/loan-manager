import LoanActions from "@/components/LoanActions";

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
};
type Audit = { id: string; loanId: string; actor: string; action: string; at: string; correlationId?: string | null; meta?: Record<string, unknown> | null };

async function fetchLoan(id: string): Promise<Loan | null> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${base}/v1/loans/${id}`, { cache: "no-store", credentials: "include" });
    if (!res.ok) return null;
    return (await res.json()) as Loan;
  } catch {
    return null;
  }
}

async function fetchAudit(id: string): Promise<Audit[]> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${base}/v1/loans/${id}/audit`, { cache: "no-store", credentials: "include" });
    if (!res.ok) return [];
    return (await res.json()) as Audit[];
  } catch {
    return [];
  }
}

export default async function LoanPage({ params }: { params: Promise<{ loanId: string }> }) {
  const { loanId } = await params;
  const [loan, audit] = await Promise.all([fetchLoan(loanId), fetchAudit(loanId)]);
  return (
    <main className="min-h-screen p-8 space-y-6">
      <h1 className="text-2xl font-semibold">Loan {loanId}</h1>
      {!loan ? (
        <div className="text-sm text-red-600">Not found</div>
      ) : (
        <div className="space-y-6 text-sm">
          <div>Status: <span className="font-medium">{loan.status}</span></div>
          <div>Client: {loan.clientId}</div>
          <div>Product: {loan.productId}</div>
          <div>Principal: {loan.principal}</div>
          <div>Interest Rate: {loan.interestRate ?? '-'}</div>
          <div>Term: {loan.termMonths} months</div>
          <div>Disbursed On: {loan.disbursedOn ?? '-'}</div>
          <LoanActions loanId={loan.id} status={loan.status} onChanged={() => {}} />
          <div>
            <h2 className="text-base font-semibold">Timeline</h2>
            <ul className="mt-2 space-y-1">
              {audit.map(e => (
                <li key={e.id} className="text-gray-300">
                  <span className="text-gray-500">{new Date(e.at).toLocaleString()}:</span> {e.action}
                  {e.actor ? <span> by <span className="font-medium">{e.actor}</span></span> : null}
                  {e.correlationId ? <span className="text-xs text-gray-500"> (cid {e.correlationId})</span> : null}
                </li>
              ))}
              {audit.length === 0 && <li className="text-gray-500">No activity yet</li>}
            </ul>
          </div>
        </div>
      )}
    </main>
  );
}


