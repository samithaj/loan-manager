"use client";
import WorkshopStatsCards from "@/components/workshop/dashboard/WorkshopStatsCards";
import QuickActions from "@/components/workshop/dashboard/QuickActions";
import RecentActivityFeed from "@/components/workshop/dashboard/RecentActivityFeed";
import JobStatusSummary from "@/components/workshop/dashboard/JobStatusSummary";

export default function WorkshopDashboard() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workshop Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Manage repair jobs, parts inventory, and stock batches
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <WorkshopStatsCards />

      {/* Quick Actions */}
      <QuickActions />

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job Pipeline */}
        <JobStatusSummary />

        {/* Recent Activity */}
        <RecentActivityFeed />
      </div>
    </div>
  );
}
