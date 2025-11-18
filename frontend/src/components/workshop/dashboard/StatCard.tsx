interface StatCardProps {
  title: string;
  value: string | number;
  icon?: string;
  trend?: "up" | "down" | "neutral" | "warning";
  subtitle?: string;
  color?: "blue" | "green" | "yellow" | "red" | "purple" | "gray";
  onClick?: () => void;
}

const colorClasses = {
  blue: "bg-blue-50 border-blue-200 text-blue-700",
  green: "bg-green-50 border-green-200 text-green-700",
  yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
  red: "bg-red-50 border-red-200 text-red-700",
  purple: "bg-purple-50 border-purple-200 text-purple-700",
  gray: "bg-gray-50 border-gray-200 text-gray-700",
};

const trendIcons = {
  up: "📈",
  down: "📉",
  neutral: "➡️",
  warning: "⚠️",
};

export default function StatCard({
  title,
  value,
  icon,
  trend,
  subtitle,
  color = "blue",
  onClick,
}: StatCardProps) {
  const isClickable = !!onClick;

  return (
    <div
      className={`
        border-2 rounded-lg p-6 transition-all
        ${colorClasses[color]}
        ${isClickable ? "cursor-pointer hover:shadow-lg hover:scale-105" : ""}
      `}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-3xl font-bold">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>
        {trend && (
          <span className="text-xl">{trendIcons[trend]}</span>
        )}
      </div>
    </div>
  );
}
