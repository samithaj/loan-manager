interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-gray-200 text-gray-800",
  SUBMITTED: "bg-blue-200 text-blue-800",
  UNDER_REVIEW: "bg-yellow-200 text-yellow-800",
  NEEDS_MORE_INFO: "bg-orange-200 text-orange-800",
  APPROVED: "bg-green-200 text-green-800",
  REJECTED: "bg-red-200 text-red-800",
  CANCELLED: "bg-gray-300 text-gray-600",
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under Review",
  NEEDS_MORE_INFO: "Needs More Info",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  CANCELLED: "Cancelled",
};

const SIZE_CLASSES: Record<string, string> = {
  sm: "px-2 py-1 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-2 text-base",
};

export default function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-block rounded-full font-semibold ${STATUS_COLORS[status]} ${SIZE_CLASSES[size]}`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}
