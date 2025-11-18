interface BikeStatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export default function BikeStatusBadge({
  status,
  size = "md",
  className = ""
}: BikeStatusBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5"
  };

  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    AVAILABLE: { bg: "bg-green-100", text: "text-green-800", label: "Available" },
    RESERVED: { bg: "bg-yellow-100", text: "text-yellow-800", label: "Reserved" },
    SOLD: { bg: "bg-blue-100", text: "text-blue-800", label: "Sold" },
    MAINTENANCE: { bg: "bg-orange-100", text: "text-orange-800", label: "In Maintenance" },
    IN_STOCK: { bg: "bg-teal-100", text: "text-teal-800", label: "In Stock" },
    ALLOCATED: { bg: "bg-purple-100", text: "text-purple-800", label: "Allocated" },
    IN_TRANSIT: { bg: "bg-indigo-100", text: "text-indigo-800", label: "In Transit" },
    WRITTEN_OFF: { bg: "bg-red-100", text: "text-red-800", label: "Written Off" }
  };

  const config = statusConfig[status] || {
    bg: "bg-gray-100",
    text: "text-gray-800",
    label: status
  };

  return (
    <span
      className={`inline-flex items-center font-semibold rounded ${config.bg} ${config.text} ${sizeClasses[size]} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${config.bg.replace('100', '500')}`} />
      {config.label}
    </span>
  );
}
