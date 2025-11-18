import { notFound } from "next/navigation";
import Link from "next/link";
import FinanceCalculator from "@/components/FinanceCalculator";
import type { Bicycle } from "@/types/bicycle";

async function getBicycle(id: string): Promise<Bicycle | null> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${baseUrl}/public/bicycles/${id}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch bicycle:", error);
    return null;
  }
}

export default async function BicycleDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const bicycle = await getBicycle(params.id);

  if (!bicycle) {
    notFound();
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const images = bicycle.image_urls.length > 0 ? bicycle.image_urls : ["/placeholder-bicycle.png"];
  const fullImages = images.map((url) =>
    url.startsWith("http") ? url : `${baseUrl}${url}`
  );

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb */}
      <div className="bg-white border-b">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          <nav className="flex items-center gap-2 text-sm">
            <Link href="/bicycles" className="text-blue-600 hover:text-blue-700">
              Home
            </Link>
            <span className="text-gray-400">/</span>
            <Link href="/bicycles/catalog" className="text-blue-600 hover:text-blue-700">
              Catalog
            </Link>
            <span className="text-gray-400">/</span>
            <span className="text-gray-600">{bicycle.title}</span>
          </nav>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Images and Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image Gallery */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="aspect-video bg-gray-100 relative">
                <img
                  src={fullImages[0]}
                  alt={bicycle.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = "/placeholder-bicycle.png";
                  }}
                />
                <div className="absolute top-4 right-4">
                  <span
                    className={`px-4 py-2 rounded-full text-sm font-semibold ${
                      bicycle.condition === "NEW"
                        ? "bg-green-500 text-white"
                        : "bg-blue-500 text-white"
                    }`}
                  >
                    {bicycle.condition}
                  </span>
                </div>
              </div>
              {fullImages.length > 1 && (
                <div className="grid grid-cols-4 gap-2 p-4">
                  {fullImages.slice(1, 5).map((url, index) => (
                    <div key={index} className="aspect-square bg-gray-100 rounded overflow-hidden">
                      <img
                        src={url}
                        alt={`${bicycle.title} - Image ${index + 2}`}
                        className="w-full h-full object-cover hover:scale-105 transition-transform cursor-pointer"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = "/placeholder-bicycle.png";
                        }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Title and Basic Info */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{bicycle.title}</h1>
              <p className="text-lg text-gray-600 mb-4">
                {bicycle.brand} {bicycle.model} - {bicycle.year}
              </p>

              <div className="flex items-center gap-6 mb-6 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>{bicycle.branch_name || bicycle.branch_id}</span>
                </div>
                {bicycle.mileage_km !== null && bicycle.mileage_km !== undefined && (
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>{bicycle.mileage_km.toLocaleString()} km</span>
                  </div>
                )}
              </div>

              {bicycle.description && (
                <div className="prose max-w-none">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-600 whitespace-pre-line">{bicycle.description}</p>
                </div>
              )}
            </div>

            {/* Specifications */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Specifications</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="border-b pb-3">
                  <div className="text-sm text-gray-600">Brand</div>
                  <div className="font-medium text-gray-900">{bicycle.brand}</div>
                </div>
                <div className="border-b pb-3">
                  <div className="text-sm text-gray-600">Model</div>
                  <div className="font-medium text-gray-900">{bicycle.model}</div>
                </div>
                <div className="border-b pb-3">
                  <div className="text-sm text-gray-600">Year</div>
                  <div className="font-medium text-gray-900">{bicycle.year}</div>
                </div>
                <div className="border-b pb-3">
                  <div className="text-sm text-gray-600">Condition</div>
                  <div className="font-medium text-gray-900">{bicycle.condition}</div>
                </div>
                {bicycle.license_plate && (
                  <div className="border-b pb-3">
                    <div className="text-sm text-gray-600">License Plate</div>
                    <div className="font-medium text-gray-900">{bicycle.license_plate}</div>
                  </div>
                )}
                {bicycle.mileage_km !== null && bicycle.mileage_km !== undefined && (
                  <div className="border-b pb-3">
                    <div className="text-sm text-gray-600">Mileage</div>
                    <div className="font-medium text-gray-900">
                      {bicycle.mileage_km.toLocaleString()} km
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Pricing Details */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Pricing</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-gray-600">Cash Price</span>
                  <span className="text-xl font-bold text-gray-900">
                    {formatCurrency(bicycle.cash_price)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-600">Hire Purchase Price</span>
                  <span className="text-xl font-bold text-blue-600">
                    {formatCurrency(bicycle.hire_purchase_price)}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                * Hire purchase price includes processing fees and documentation charges.
              </p>
            </div>
          </div>

          {/* Right Column - Finance Calculator */}
          <div className="lg:col-span-1">
            <FinanceCalculator
              bicycleId={bicycle.id}
              cashPrice={bicycle.cash_price}
              hirePurchasePrice={bicycle.hire_purchase_price}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
