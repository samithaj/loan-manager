"use client";
import { useEffect, useMemo, useState } from "react";
import { PagedTable, Column } from "./PagedTable";

type Vehicle = {
  id: string;
  vinOrFrameNumber?: string | null;
  brand: string;
  model: string;
  plate?: string | null;
  color?: string | null;
  purchasePrice?: number | null;
  msrp?: number | null;
  status: string;
  linkedLoanId?: string | null;
};

type Loan = { id: string; clientId: string };

function authHeaders() {
  if (typeof window === "undefined") return {} as Record<string, string>;
  const u = localStorage.getItem("u") || "";
  const p = localStorage.getItem("p") || "";
  return u && p ? { Authorization: "Basic " + btoa(`${u}:${p}`) } : {};
}

export default function VehicleInventoryManager() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [form, setForm] = useState({
    vinOrFrameNumber: "",
    brand: "",
    model: "",
    plate: "",
    color: "",
    purchasePrice: "",
    msrp: ""
  });
  const [showAllocationModal, setShowAllocationModal] = useState(false);
  const [allocatingVehicle, setAllocatingVehicle] = useState<Vehicle | null>(null);
  const [selectedLoanId, setSelectedLoanId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const vehiclesUrl = new URL(`${base}/v1/vehicle-inventory`);
      if (statusFilter) {
        vehiclesUrl.searchParams.set("status", statusFilter);
      }

      const [vehiclesRes, loansRes] = await Promise.all([
        fetch(vehiclesUrl.toString(), { cache: "no-store", headers: authHeaders() }),
        fetch(`${base}/v1/loans`, { cache: "no-store", headers: authHeaders() })
      ]);

      if (vehiclesRes.ok) {
        const vehiclesData = await vehiclesRes.json();
        setVehicles(vehiclesData);
      }

      if (loansRes.ok) {
        const loansData = await loansRes.json();
        setLoans(loansData);
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
  }, [statusFilter]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const payload = {
      id: editingVehicle?.id || `V${Date.now()}`,
      vinOrFrameNumber: form.vinOrFrameNumber || undefined,
      brand: form.brand,
      model: form.model,
      plate: form.plate || undefined,
      color: form.color || undefined,
      purchasePrice: form.purchasePrice ? parseFloat(form.purchasePrice) : undefined,
      msrp: form.msrp ? parseFloat(form.msrp) : undefined
    };

    try {
      const method = editingVehicle ? "PUT" : "POST";
      const url = editingVehicle 
        ? `${base}/v1/vehicle-inventory/${editingVehicle.id}`
        : `${base}/v1/vehicle-inventory`;
      
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      resetForm();
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function onDelete(vehicleId: string) {
    if (!confirm("Are you sure you want to delete this vehicle?")) return;
    
    setError(null);
    try {
      const res = await fetch(`${base}/v1/vehicle-inventory/${vehicleId}`, {
        method: "DELETE",
        headers: authHeaders()
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function allocateVehicle() {
    if (!allocatingVehicle || !selectedLoanId) return;
    
    setError(null);
    try {
      const res = await fetch(
        `${base}/v1/vehicle-inventory/${allocatingVehicle.id}/allocate?loanId=${selectedLoanId}`,
        { method: "POST", headers: authHeaders() }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      setShowAllocationModal(false);
      setAllocatingVehicle(null);
      setSelectedLoanId("");
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function releaseVehicle(vehicleId: string) {
    if (!confirm("Are you sure you want to release this vehicle?")) return;
    
    setError(null);
    try {
      const res = await fetch(
        `${base}/v1/vehicle-inventory/${vehicleId}/release`,
        { method: "POST", headers: authHeaders() }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || `Failed: ${res.status}`);
      }

      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function startEdit(vehicle: Vehicle) {
    setEditingVehicle(vehicle);
    setForm({
      vinOrFrameNumber: vehicle.vinOrFrameNumber || "",
      brand: vehicle.brand,
      model: vehicle.model,
      plate: vehicle.plate || "",
      color: vehicle.color || "",
      purchasePrice: vehicle.purchasePrice?.toString() || "",
      msrp: vehicle.msrp?.toString() || ""
    });
    setShowForm(true);
  }

  function resetForm() {
    setForm({
      vinOrFrameNumber: "",
      brand: "",
      model: "",
      plate: "",
      color: "",
      purchasePrice: "",
      msrp: ""
    });
    setEditingVehicle(null);
    setShowForm(false);
  }

  const statusBadgeColor = (status: string) => {
    switch (status) {
      case "IN_STOCK": return "bg-green-100 text-green-800";
      case "ALLOCATED": return "bg-yellow-100 text-yellow-800";
      case "SOLD": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const columns: Column<Vehicle>[] = useMemo(() => [
    { key: "brand", label: "Brand", render: (vehicle) => vehicle.brand },
    { key: "model", label: "Model", render: (vehicle) => vehicle.model },
    { key: "vinOrFrameNumber", label: "VIN/Frame", render: (vehicle) => vehicle.vinOrFrameNumber || "—" },
    { key: "plate", label: "Plate", render: (vehicle) => vehicle.plate || "—" },
    { key: "color", label: "Color", render: (vehicle) => vehicle.color || "—" },
    { key: "purchasePrice", label: "Purchase Price", render: (vehicle) => 
      vehicle.purchasePrice ? `$${vehicle.purchasePrice.toLocaleString()}` : "—"
    },
    { key: "status", label: "Status", render: (vehicle) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadgeColor(vehicle.status)}`}>
        {vehicle.status}
      </span>
    )},
    { key: "linkedLoanId", label: "Linked Loan", render: (vehicle) => vehicle.linkedLoanId || "—" },
    {
      key: "actions",
      label: "Actions",
      render: (vehicle) => (
        <div className="flex gap-2">
          {vehicle.status !== "SOLD" && (
            <button
              onClick={() => startEdit(vehicle)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Edit
            </button>
          )}
          {vehicle.status === "IN_STOCK" && (
            <button
              onClick={() => {
                setAllocatingVehicle(vehicle);
                setShowAllocationModal(true);
              }}
              className="text-green-600 hover:text-green-800 text-sm"
            >
              Allocate
            </button>
          )}
          {vehicle.status === "ALLOCATED" && (
            <button
              onClick={() => releaseVehicle(vehicle.id)}
              className="text-yellow-600 hover:text-yellow-800 text-sm"
            >
              Release
            </button>
          )}
          {vehicle.status !== "SOLD" && (
            <button
              onClick={() => onDelete(vehicle.id)}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Delete
            </button>
          )}
        </div>
      ),
    },
  ], []);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex gap-4 items-center">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Status</option>
          <option value="IN_STOCK">In Stock</option>
          <option value="ALLOCATED">Allocated</option>
          <option value="SOLD">Sold</option>
        </select>
        
        <button
          onClick={() => {
            setEditingVehicle(null);
            resetForm();
            setShowForm(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Vehicle
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Table */}
      <PagedTable
        columns={columns}
        data={vehicles}
        loading={loading}
        className="bg-white rounded-lg shadow"
      />

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">
              {editingVehicle ? "Edit Vehicle" : "Add Vehicle"}
            </h3>
            
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Brand *
                  </label>
                  <input
                    type="text"
                    value={form.brand}
                    onChange={(e) => setForm({ ...form, brand: e.target.value })}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model *
                  </label>
                  <input
                    type="text"
                    value={form.model}
                    onChange={(e) => setForm({ ...form, model: e.target.value })}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    VIN/Frame Number
                  </label>
                  <input
                    type="text"
                    value={form.vinOrFrameNumber}
                    onChange={(e) => setForm({ ...form, vinOrFrameNumber: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plate Number
                  </label>
                  <input
                    type="text"
                    value={form.plate}
                    onChange={(e) => setForm({ ...form, plate: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Color
                  </label>
                  <input
                    type="text"
                    value={form.color}
                    onChange={(e) => setForm({ ...form, color: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Purchase Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.purchasePrice}
                    onChange={(e) => setForm({ ...form, purchasePrice: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    MSRP
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.msrp}
                    onChange={(e) => setForm({ ...form, msrp: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingVehicle ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Allocation Modal */}
      {showAllocationModal && allocatingVehicle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium mb-4">
              Allocate Vehicle to Loan
            </h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Vehicle: {allocatingVehicle.brand} {allocatingVehicle.model}
              </p>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Loan *
              </label>
              <select
                value={selectedLoanId}
                onChange={(e) => setSelectedLoanId(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a loan</option>
                {loans.filter(loan => loan.status === "APPROVED").map((loan) => (
                  <option key={loan.id} value={loan.id}>
                    {loan.id} - {loan.clientId}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowAllocationModal(false);
                  setAllocatingVehicle(null);
                  setSelectedLoanId("");
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={allocateVehicle}
                disabled={!selectedLoanId}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                Allocate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}