import Link from "next/link";

interface QuickAction {
  label: string;
  href?: string;
  onClick?: () => void;
  icon: string;
  color: "blue" | "green" | "purple" | "orange";
}

const colorClasses = {
  blue: "bg-blue-600 hover:bg-blue-700",
  green: "bg-green-600 hover:bg-green-700",
  purple: "bg-purple-600 hover:bg-purple-700",
  orange: "bg-orange-600 hover:bg-orange-700",
};

export default function QuickActions() {
  const actions: QuickAction[] = [
    {
      label: "New Repair Job",
      href: "/workshop/jobs/new",
      icon: "🔧",
      color: "blue",
    },
    {
      label: "Receive Stock",
      href: "/workshop/stock-batches?action=receive",
      icon: "📦",
      color: "green",
    },
    {
      label: "Search Parts",
      href: "/workshop/parts",
      icon: "🔍",
      color: "purple",
    },
    {
      label: "View Reports",
      href: "/workshop/reports",
      icon: "📊",
      color: "orange",
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {actions.map((action) => {
          const button = (
            <button
              type="button"
              onClick={action.onClick}
              className={`
                ${colorClasses[action.color]}
                text-white px-4 py-6 rounded-lg
                transition-all hover:shadow-lg hover:scale-105
                flex flex-col items-center justify-center gap-2
                font-medium text-center
              `}
            >
              <span className="text-3xl">{action.icon}</span>
              <span className="text-sm">{action.label}</span>
            </button>
          );

          return action.href ? (
            <Link key={action.label} href={action.href}>
              {button}
            </Link>
          ) : (
            <div key={action.label}>{button}</div>
          );
        })}
      </div>
    </div>
  );
}
