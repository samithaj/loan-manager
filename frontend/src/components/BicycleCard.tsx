import Link from "next/link";
import type { Bicycle } from "@/types/bicycle";

interface BicycleCardProps {
  bicycle: Bicycle;
}

export default function BicycleCard({ bicycle }: BicycleCardProps) {
  const imageUrl = bicycle.thumbnail_url || bicycle.image_urls[0] || "/placeholder-bicycle.png";
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const fullImageUrl = imageUrl.startsWith("http") ? imageUrl : `${baseUrl}${imageUrl}`;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const monthlyPayment = bicycle.monthly_payment_estimate || (bicycle.hire_purchase_price / 36);

  return (
    <Link href={`/bicycles/${bicycle.id}`} className="group">
      <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 h-full flex flex-col">
        {/* Image */}
        <div className="relative h-48 bg-gray-100 overflow-hidden">
          <img
            src={fullImageUrl}
            alt={bicycle.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = "/placeholder-bicycle.png";
            }}
          />
          {/* Condition Badge */}
          <div className="absolute top-2 right-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                bicycle.condition === "NEW"
                  ? "bg-green-500 text-white"
                  : "bg-blue-500 text-white"
              }`}
            >
              {bicycle.condition}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 flex-1 flex flex-col">
          {/* Title */}
          <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
            {bicycle.title}
          </h3>

          {/* Brand and Model */}
          <p className="text-sm text-gray-600 mb-2">
            {bicycle.brand} {bicycle.model} ({bicycle.year})
          </p>

          {/* Mileage */}
          {bicycle.mileage_km !== null && bicycle.mileage_km !== undefined && (
            <p className="text-xs text-gray-500 mb-3">
              {bicycle.mileage_km.toLocaleString()} km
            </p>
          )}

          {/* Spacer */}
          <div className="flex-1" />

          {/* Pricing */}
          <div className="mt-auto pt-3 border-t">
            <div className="flex items-baseline justify-between mb-1">
              <span className="text-xs text-gray-500">Cash Price</span>
              <span className="text-sm font-medium text-gray-700">
                {formatCurrency(bicycle.cash_price)}
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-gray-500">From/month</span>
              <span className="text-lg font-bold text-blue-600">
                {formatCurrency(monthlyPayment)}
              </span>
            </div>
          </div>

          {/* CTA */}
          <button className="mt-3 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm">
            View Details
          </button>
        </div>
      </div>
    </Link>
  );
}
