export type JobStatus = "OPEN" | "IN_PROGRESS" | "COMPLETED" | "INVOICED" | "CANCELLED";

const statusColors: Record<JobStatus, string> = {
  OPEN: "bg-yellow-100 text-yellow-800 border-yellow-200",
  IN_PROGRESS: "bg-blue-100 text-blue-800 border-blue-200",
  COMPLETED: "bg-green-100 text-green-800 border-green-200",
  INVOICED: "bg-purple-100 text-purple-800 border-purple-200",
  CANCELLED: "bg-red-100 text-red-800 border-red-200",
};

const statusIcons: Record<JobStatus, string> = {
  OPEN: "🔓",
  IN_PROGRESS: "⚙️",
  COMPLETED: "✅",
  INVOICED: "💰",
  CANCELLED: "❌",
};

interface StatusBadgeProps {
  status: JobStatus;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
}

export default function StatusBadge({ status, size = "md", showIcon = true }: StatusBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
    lg: "px-4 py-1.5 text-base",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${statusColors[status]} ${sizeClasses[size]}`}
    >
      {showIcon && <span>{statusIcons[status]}</span>}
      {status.replace(/_/g, " ")}
    </span>
  );
}
