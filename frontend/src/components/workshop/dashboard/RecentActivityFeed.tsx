"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import StatusBadge, { JobStatus } from "../common/StatusBadge";

interface ActivityItem {
  id: string;
  type: "job_created" | "job_completed" | "stock_received" | "low_stock_alert" | "part_added";
  timestamp: string;
  message: string;
  link?: string;
  status?: JobStatus;
  severity?: "info" | "warning" | "success";
}

export default function RecentActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    async function fetchActivities() {
      try {
        // Fetch recent jobs
        const jobsRes = await fetch(`${base}/v1/workshop/jobs?limit=5&sort=-opened_at`, {
          credentials: "include",
        });
        if (jobsRes.ok) {
          const jobs = await jobsRes.json();
          const jobActivities: ActivityItem[] = jobs.map((job: any) => ({
            id: `job-${job.id}`,
            type: job.status === "COMPLETED" ? "job_completed" : "job_created",
            timestamp: job.opened_at || job.created_at,
            message: `Job #${job.job_number} ${job.status === "COMPLETED" ? "completed" : "opened"} for ${job.bicycle?.license_plate || "bike"}`,
            link: `/workshop/jobs/${job.id}`,
            status: job.status,
            severity: job.status === "COMPLETED" ? "success" : "info",
          }));
          setActivities(jobActivities);
        }
      } catch (error) {
        console.error("Failed to fetch activities:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchActivities();
  }, []);

  const severityColors = {
    info: "bg-blue-50 border-blue-200",
    warning: "bg-yellow-50 border-yellow-200",
    success: "bg-green-50 border-green-200",
  };

  const typeIcons = {
    job_created: "🆕",
    job_completed: "✅",
    stock_received: "📦",
    low_stock_alert: "⚠️",
    part_added: "🔧",
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center text-gray-500 py-8">Loading activities...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
      {activities.length === 0 ? (
        <div className="text-center text-gray-500 py-8">No recent activity</div>
      ) : (
        <div className="space-y-3">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className={`
                border-l-4 p-4 rounded-r-lg
                ${severityColors[activity.severity || "info"]}
                transition-all hover:shadow-md
              `}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{typeIcons[activity.type]}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                    {activity.status && <StatusBadge status={activity.status} size="sm" />}
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-600">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                    {activity.link && (
                      <Link
                        href={activity.link}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View Details →
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
