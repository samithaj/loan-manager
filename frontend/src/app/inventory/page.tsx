"use client";
import VehicleInventoryManager from "../../components/VehicleInventoryManager";

export default function InventoryPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Vehicle Inventory</h1>
        <p className="text-gray-600 mt-2">Manage vehicle inventory and loan allocations</p>
      </div>
      
      <VehicleInventoryManager />
    </div>
  );
}