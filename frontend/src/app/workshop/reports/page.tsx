"use client";

export default function WorkshopReportsPage() {
  const reports = [
    {
      title: "Job Profitability Report",
      description: "Analyze profit margins and revenue from repair jobs",
      icon: "💰",
      color: "bg-green-100 border-green-200 text-green-700",
    },
    {
      title: "Parts Inventory Report",
      description: "Stock levels, valuation, and reorder recommendations",
      icon: "📦",
      color: "bg-blue-100 border-blue-200 text-blue-700",
    },
    {
      title: "Mechanic Performance Report",
      description: "Track mechanic productivity and job completion rates",
      icon: "👷",
      color: "bg-purple-100 border-purple-200 text-purple-700",
    },
    {
      title: "Bike Overhaul Cost Report",
      description: "Complete cost analysis for bikes being prepared for sale",
      icon: "🏍️",
      color: "bg-orange-100 border-orange-200 text-orange-700",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Workshop Reports</h1>
        <p className="text-gray-600 mt-1">
          Analyze workshop performance, inventory, and profitability
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((report) => (
          <div
            key={report.title}
            className={`border-2 rounded-lg p-6 cursor-pointer hover:shadow-lg transition-all ${report.color}`}
          >
            <div className="flex items-start gap-4">
              <span className="text-5xl">{report.icon}</span>
              <div className="flex-1">
                <h2 className="text-xl font-bold mb-2">{report.title}</h2>
                <p className="text-sm opacity-80">{report.description}</p>
                <button className="mt-4 px-4 py-2 bg-white rounded-lg text-sm font-medium hover:bg-opacity-90 transition-colors">
                  View Report →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-2">Report Features (Coming Soon)</h3>
        <ul className="text-sm text-gray-700 space-y-2 list-disc list-inside">
          <li>Customizable date ranges and filters</li>
          <li>Export to CSV and PDF formats</li>
          <li>Interactive charts and visualizations</li>
          <li>Scheduled email delivery</li>
          <li>Comparison across branches</li>
        </ul>
      </div>
    </div>
  );
}
