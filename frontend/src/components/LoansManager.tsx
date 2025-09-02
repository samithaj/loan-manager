"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";
import Link from "next/link";

type Loan = {
  id: string;
  clientId: string;
  productId: string;
  principal: number;
  interestRate?: number | null;
  termMonths: number;
  status: string;
  disbursedOn?: string | null;
  createdOn: string;
};

type Client = { id: string; displayName: string };
type LoanProduct = { id: string; name: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function LoansManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [rows, setRows] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<{
    id: string;
    clientId: string;
    productId: string;
    principal: string;
    interestRate: string;
    termMonths: string;
  }>({ id: "", clientId: "", productId: "", principal: "", interestRate: "", termMonths: "" });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<LoanProduct[]>([]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      // Load loans
      const loansUrl = new URL(`${base}/v1/loans`);
      if (q) loansUrl.searchParams.set("q", q);
      const loansRes = await fetch(loansUrl.toString(), { cache: "no-store", headers: authHeaders() });
      if (!loansRes.ok) throw new Error(`Failed to load loans: ${loansRes.status}`);
      const loansData = (await loansRes.json()) as Loan[];
      setRows(loansData);

      // Load clients and products for form
      const [clientsRes, productsRes] = await Promise.all([
        fetch(`${base}/v1/clients`, { cache: "no-store", headers: authHeaders() }),
        fetch(`${base}/v1/loan-products`, { cache: "no-store", headers: authHeaders() })
      ]);

      if (clientsRes.ok) {
        const clientsData = await clientsRes.json();
        setClients(clientsData);
      }
      if (productsRes.ok) {
        const productsData = await productsRes.json();
        setProducts(productsData);
      }
    } catch {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    
    const payload = {
      id: form.id || `L${Date.now()}`,
      clientId: form.clientId,
      productId: form.productId,
      principal: parseFloat(form.principal),
      interestRate: form.interestRate ? parseFloat(form.interestRate) : undefined,
      termMonths: form.termMonths ? parseInt(form.termMonths) : undefined,
    };

    try {
      const method = editingId ? "PUT" : "POST";
      const url = editingId ? `${base}/v1/loans/${editingId}` : `${base}/v1/loans`;
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }
      setForm({ id: "", clientId: "", productId: "", principal: "", interestRate: "", termMonths: "" });
      setEditingId(null);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function onEdit(loan: Loan) {
    setForm({
      id: loan.id,
      clientId: loan.clientId,
      productId: loan.productId,
      principal: loan.principal.toString(),
      interestRate: loan.interestRate?.toString() || "",
      termMonths: loan.termMonths.toString(),
    });
    setEditingId(loan.id);
  }

  function onCancel() {
    setForm({ id: "", clientId: "", productId: "", principal: "", interestRate: "", termMonths: "" });
    setEditingId(null);
  }

  const statusBadgeColor = (status: string) => {
    switch (status) {
      case "PENDING": return "bg-yellow-100 text-yellow-800";
      case "APPROVED": return "bg-blue-100 text-blue-800";
      case "DISBURSED": return "bg-green-100 text-green-800";
      case "CLOSED": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const clientName = (clientId: string) => clients.find(c => c.id === clientId)?.displayName || clientId;
  const productName = (productId: string) => products.find(p => p.id === productId)?.name || productId;

  const columns: Column<Loan>[] = useMemo(() => [
    { key: "id", label: "Loan ID", render: (loan) => (
      <Link href={`/loans/${loan.id}`} className="text-blue-600 hover:text-blue-800 font-medium">
        {loan.id}
      </Link>
    )},
    { key: "clientId", label: "Client", render: (loan) => clientName(loan.clientId) },
    { key: "productId", label: "Product", render: (loan) => productName(loan.productId) },
    { key: "principal", label: "Principal", render: (loan) => `$${loan.principal.toLocaleString()}` },
    { key: "status", label: "Status", render: (loan) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadgeColor(loan.status)}`}>
        {loan.status}
      </span>
    )},
    { key: "createdOn", label: "Created", render: (loan) => new Date(loan.createdOn).toLocaleDateString() },
    {
      key: "actions",
      label: "Actions",
      render: (loan) => (
        <div className="flex gap-2">
          {loan.status === "PENDING" && (
            <button
              onClick={() => onEdit(loan)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Edit
            </button>
          )}
          <Link href={`/loans/${loan.id}`} className="text-green-600 hover:text-green-800 text-sm">
            View
          </Link>
        </div>
      ),
    },
  ], [clients, products]);

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Search loans..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Form */}
      <form onSubmit={onSubmit} className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">{editingId ? "Edit Loan" : "Create Loan"}</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Client *</label>
            <select
              value={form.clientId}
              onChange={(e) => setForm({ ...form, clientId: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a client</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.displayName}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product *</label>
            <select
              value={form.productId}
              onChange={(e) => setForm({ ...form, productId: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a product</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Principal *</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.principal}
              onChange={(e) => setForm({ ...form, principal: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Interest Rate (%)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="100"
              value={form.interestRate}
              onChange={(e) => setForm({ ...form, interestRate: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Term (Months)</label>
            <input
              type="number"
              min="1"
              value={form.termMonths}
              onChange={(e) => setForm({ ...form, termMonths: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {editingId ? "Update" : "Create"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Table */}
      <PagedTable
        columns={columns}
        data={rows}
        loading={loading}
        className="bg-white rounded-lg shadow"
      />
    </div>
  );
}