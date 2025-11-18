"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import BicycleForm from "@/components/BicycleForm";
import type { Bicycle } from "@/types/bicycle";

export default function EditBicyclePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const [bicycle, setBicycle] = useState<Bicycle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadBicycle() {
      try {
        const res = await fetch(`${baseUrl}/v1/bicycles/${params.id}`, {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch bicycle");
        }

        const data: Bicycle = await res.json();
        setBicycle(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load bicycle");
      } finally {
        setLoading(false);
      }
    }

    loadBicycle();
  }, [baseUrl, params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
      </div>
    );
  }

  if (error || !bicycle) {
    return (
      <div className="min-h-screen max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-600">{error || "Bicycle not found"}</p>
          <Link href="/inventory" className="text-blue-600 hover:text-blue-700 underline mt-4 inline-block">
            Back to Inventory
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/inventory" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">
          ← Back to Inventory
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Bicycle</h1>
        <p className="text-gray-600 font-mono">{bicycle.id}</p>
      </div>

      <BicycleForm bicycle={bicycle} isEdit />
    </div>
  );
}
