interface StockNumberBadgeProps {
  stockNumber: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export default function StockNumberBadge({
  stockNumber,
  size = "md",
  className = ""
}: StockNumberBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5"
  };

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold bg-gray-100 text-gray-800 rounded ${sizeClasses[size]} ${className}`}
      title={`Stock Number: ${stockNumber}`}
    >
      <svg
        className="w-3 h-3 mr-1.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
        />
      </svg>
      {stockNumber}
    </span>
  );
}
