"use client";
import { useState, useEffect } from "react";

interface Mechanic {
  id: number;
  display_name: string;
  email?: string;
  photo_url?: string;
  branch_id?: number;
  branch_name?: string;
}

interface MechanicSelectorProps {
  value: number | null;
  onChange: (mechanicId: number | null) => void;
  label?: string;
  branchId?: number;
  required?: boolean;
  className?: string;
}

export default function MechanicSelector({
  value,
  onChange,
  label = "Assign Mechanic",
  branchId,
  required = false,
  className = "",
}: MechanicSelectorProps) {
  const [mechanics, setMechanics] = useState<Mechanic[]>([]);
  const [loading, setLoading] = useState(true);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    async function fetchMechanics() {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          role: "mechanic",
          ...(branchId && { branch_id: branchId.toString() }),
        });
        const res = await fetch(`${base}/v1/reference/staff?${params}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setMechanics(data);
        }
      } catch (error) {
        console.error("Failed to fetch mechanics:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchMechanics();
  }, [branchId]);

  const selectedMechanic = mechanics.find((m) => m.id === value);

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {loading ? (
        <div className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
          Loading mechanics...
        </div>
      ) : (
        <div className="space-y-2">
          <select
            value={value || ""}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
            required={required}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a mechanic...</option>
            {mechanics.map((mechanic) => (
              <option key={mechanic.id} value={mechanic.id}>
                {mechanic.display_name}
                {mechanic.branch_name && ` (${mechanic.branch_name})`}
              </option>
            ))}
          </select>

          {selectedMechanic && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              {selectedMechanic.photo_url ? (
                <img
                  src={selectedMechanic.photo_url}
                  alt={selectedMechanic.display_name}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-semibold">
                  {selectedMechanic.display_name.charAt(0).toUpperCase()}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900">{selectedMechanic.display_name}</div>
                {selectedMechanic.email && (
                  <div className="text-sm text-gray-600">{selectedMechanic.email}</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
