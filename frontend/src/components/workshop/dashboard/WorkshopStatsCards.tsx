"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import StatCard from "./StatCard";

interface WorkshopStats {
  activeJobs: number;
  lowStockItems: number;
  jobsCompletedToday: number;
  todayRevenue: number;
  partsValue: number;
  averageMargin: number;
}

export default function WorkshopStatsCards() {
  const router = useRouter();
  const [stats, setStats] = useState<WorkshopStats>({
    activeJobs: 0,
    lowStockItems: 0,
    jobsCompletedToday: 0,
    todayRevenue: 0,
    partsValue: 0,
    averageMargin: 0,
  });
  const [loading, setLoading] = useState(true);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    async function fetchStats() {
      try {
        // Fetch jobs
        const jobsRes = await fetch(`${base}/v1/workshop/jobs`, { credentials: "include" });
        const jobs = jobsRes.ok ? await jobsRes.json() : [];

        const activeJobs = jobs.filter(
          (j: any) => j.status === "OPEN" || j.status === "IN_PROGRESS"
        ).length;

        const today = new Date().toISOString().split("T")[0];
        const completedToday = jobs.filter(
          (j: any) =>
            j.status === "COMPLETED" && j.completed_at?.startsWith(today)
        );
        const jobsCompletedToday = completedToday.length;
        const todayRevenue = completedToday.reduce(
          (sum: number, j: any) => sum + (j.total_price || 0),
          0
        );

        // Calculate average margin
        const invoicedJobs = jobs.filter(
          (j: any) => j.total_cost > 0 && j.total_price > 0
        );
        const averageMargin =
          invoicedJobs.length > 0
            ? invoicedJobs.reduce((sum: number, j: any) => {
                const margin =
                  ((j.total_price - j.total_cost) / j.total_price) * 100;
                return sum + margin;
              }, 0) / invoicedJobs.length
            : 0;

        // Fetch parts summary
        const partsRes = await fetch(`${base}/v1/workshop/parts/summary`, {
          credentials: "include",
        });
        const partsSummary = partsRes.ok ? await partsRes.json() : [];

        const partsValue = partsSummary.reduce(
          (sum: number, p: any) => sum + (p.total_value || 0),
          0
        );
        const lowStockItems = partsSummary.filter(
          (p: any) => p.total_quantity < (p.minimum_stock_level || 0)
        ).length;

        setStats({
          activeJobs,
          lowStockItems,
          jobsCompletedToday,
          todayRevenue,
          partsValue,
          averageMargin,
        });
      } catch (error) {
        console.error("Failed to fetch workshop stats:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-gray-100 rounded-lg p-6 h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Active Jobs"
        value={stats.activeJobs}
        icon="🔧"
        color="blue"
        subtitle="Open + In Progress"
        onClick={() => router.push("/workshop/jobs?status=OPEN,IN_PROGRESS")}
      />
      <StatCard
        title="Low Stock Alerts"
        value={stats.lowStockItems}
        icon="⚠️"
        color={stats.lowStockItems > 0 ? "red" : "green"}
        trend={stats.lowStockItems > 0 ? "warning" : "neutral"}
        subtitle="Below minimum level"
        onClick={() => router.push("/workshop/parts?low_stock=true")}
      />
      <StatCard
        title="Completed Today"
        value={stats.jobsCompletedToday}
        icon="✅"
        color="green"
        subtitle="Jobs finished"
      />
      <StatCard
        title="Today's Revenue"
        value={`$${stats.todayRevenue.toLocaleString()}`}
        icon="💰"
        color="purple"
        subtitle="From completed jobs"
      />
      <StatCard
        title="Parts Inventory Value"
        value={`$${stats.partsValue.toLocaleString()}`}
        icon="📦"
        color="gray"
        subtitle="Total stock value"
        onClick={() => router.push("/workshop/parts")}
      />
      <StatCard
        title="Average Margin"
        value={`${stats.averageMargin.toFixed(1)}%`}
        icon="📊"
        color="blue"
        subtitle="On completed jobs"
        trend={stats.averageMargin > 25 ? "up" : "neutral"}
      />
    </div>
  );
}
