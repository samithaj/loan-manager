import Link from "next/link";
import StockNumberBadge from "./StockNumberBadge";
import BikeStatusBadge from "./BikeStatusBadge";

interface BikeStockCardProps {
  bike: {
    id: string;
    title: string;
    brand: string;
    model: string;
    year: number;
    current_stock_number?: string;
    status: string;
    company_id: string;
    current_branch_id?: string;
    base_purchase_price?: number;
    selling_price?: number;
    profit_or_loss?: number;
    thumbnail_url?: string;
    image_urls: string[];
  };
  showActions?: boolean;
  onTransfer?: (bikeId: string) => void;
  onSell?: (bikeId: string) => void;
  onView?: (bikeId: string) => void;
}

export default function BikeStockCard({
  bike,
  showActions = true,
  onTransfer,
  onSell,
  onView
}: BikeStockCardProps) {
  const imageUrl = bike.thumbnail_url || bike.image_urls[0] || "/placeholder-bicycle.png";
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const fullImageUrl = imageUrl.startsWith("http") ? imageUrl : `${baseUrl}${imageUrl}`;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const profitColor = bike.profit_or_loss
    ? bike.profit_or_loss > 0
      ? "text-green-600"
      : bike.profit_or_loss < 0
      ? "text-red-600"
      : "text-gray-600"
    : "text-gray-400";

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 h-full flex flex-col">
      {/* Image */}
      <div className="relative h-40 bg-gray-100 overflow-hidden">
        <img
          src={fullImageUrl}
          alt={bike.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = "/placeholder-bicycle.png";
          }}
        />
        {/* Stock Number Badge */}
        {bike.current_stock_number && (
          <div className="absolute top-2 left-2">
            <StockNumberBadge stockNumber={bike.current_stock_number} size="sm" />
          </div>
        )}
        {/* Status Badge */}
        <div className="absolute top-2 right-2">
          <BikeStatusBadge status={bike.status} size="sm" />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex-1 flex flex-col">
        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-1">
          {bike.title}
        </h3>

        {/* Brand and Model */}
        <p className="text-sm text-gray-600 mb-3">
          {bike.brand} {bike.model} ({bike.year})
        </p>

        {/* Company & Branch */}
        <div className="text-xs text-gray-500 mb-3">
          <div>Company: <span className="font-medium">{bike.company_id}</span></div>
          {bike.current_branch_id && (
            <div>Branch: <span className="font-medium">{bike.current_branch_id}</span></div>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Financial Info */}
        <div className="mt-auto pt-3 border-t space-y-1">
          {bike.base_purchase_price !== null && bike.base_purchase_price !== undefined && (
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-gray-500">Purchase Price</span>
              <span className="text-sm font-medium text-gray-700">
                {formatCurrency(bike.base_purchase_price)}
              </span>
            </div>
          )}
          {bike.selling_price !== null && bike.selling_price !== undefined && (
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-gray-500">Selling Price</span>
              <span className="text-sm font-medium text-gray-700">
                {formatCurrency(bike.selling_price)}
              </span>
            </div>
          )}
          {bike.profit_or_loss !== null && bike.profit_or_loss !== undefined && (
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-gray-500">P/L</span>
              <span className={`text-sm font-bold ${profitColor}`}>
                {formatCurrency(bike.profit_or_loss)}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        {showActions && (
          <div className="mt-3 flex gap-2">
            <Link
              href={`/bikes/${bike.id}`}
              className="flex-1 text-center bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
            >
              View
            </Link>
            {onTransfer && bike.status === "IN_STOCK" && (
              <button
                onClick={() => onTransfer(bike.id)}
                className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
              >
                Transfer
              </button>
            )}
            {onSell && bike.status === "IN_STOCK" && (
              <button
                onClick={() => onSell(bike.id)}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors font-medium text-sm"
              >
                Sell
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
