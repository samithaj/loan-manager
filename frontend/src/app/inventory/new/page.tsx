import BicycleForm from "@/components/BicycleForm";
import Link from "next/link";

export default function NewBicyclePage() {
  return (
    <div className="min-h-screen max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/inventory" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
          ← Back to Inventory
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Add New Bicycle</h1>
        <p className="text-gray-600">Fill in the details to add a new bicycle to your inventory</p>
      </div>

      <BicycleForm />
    </div>
  );
}
