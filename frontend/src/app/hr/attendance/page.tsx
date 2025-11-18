"use client";

import { useState, useEffect } from "react";

interface AttendanceRecord {
  id: string;
  user_id: string;
  date: string;
  clock_in?: string;
  clock_out?: string;
  status: string;
  work_hours?: number;
  overtime_hours: number;
  notes?: string;
  location?: string;
}

export default function AttendancePage() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [clockingIn, setClockingIn] = useState(false);

  useEffect(() => {
    fetchRecords();
    fetchTodayRecord();
  }, []);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const dateFrom = new Date();
      dateFrom.setDate(dateFrom.getDate() - 30); // Last 30 days

      const params = new URLSearchParams({
        date_from: dateFrom.toISOString().split("T")[0],
        limit: "30"
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/attendance/records?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setRecords(data.items || []);
      }
    } catch (error) {
      console.error("Error fetching attendance records:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTodayRecord = async () => {
    try {
      const params = new URLSearchParams({
        date_from: new Date().toISOString().split("T")[0],
        date_to: new Date().toISOString().split("T")[0],
        limit: "1"
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/attendance/records?${params}`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.items && data.items.length > 0) {
          setTodayRecord(data.items[0]);
        }
      }
    } catch (error) {
      console.error("Error fetching today's record:", error);
    }
  };

  const handleClockIn = async () => {
    try {
      setClockingIn(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/attendance/clock-in`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTodayRecord(data);
        alert("Clocked in successfully!");
        fetchRecords();
      } else {
        const error = await response.json();
        alert(`Failed to clock in: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error clocking in:", error);
      alert("An error occurred while clocking in");
    } finally {
      setClockingIn(false);
    }
  };

  const handleClockOut = async () => {
    try {
      setClockingIn(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/attendance/clock-out`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTodayRecord(data);
        alert("Clocked out successfully!");
        fetchRecords();
      } else {
        const error = await response.json();
        alert(`Failed to clock out: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error clocking out:", error);
      alert("An error occurred while clocking out");
    } finally {
      setClockingIn(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PRESENT":
        return "bg-green-100 text-green-800";
      case "ABSENT":
        return "bg-red-100 text-red-800";
      case "LATE":
        return "bg-yellow-100 text-yellow-800";
      case "HALF_DAY":
        return "bg-orange-100 text-orange-800";
      case "ON_LEAVE":
        return "bg-blue-100 text-blue-800";
      case "HOLIDAY":
        return "bg-purple-100 text-purple-800";
      case "WEEKEND":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const canClockIn = !todayRecord || !todayRecord.clock_in;
  const canClockOut = todayRecord && todayRecord.clock_in && !todayRecord.clock_out;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Attendance Tracking</h1>

      {/* Today's Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Today's Attendance</h2>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="text-sm text-gray-600">
              Date: <span className="font-semibold">{new Date().toLocaleDateString()}</span>
            </div>
            {todayRecord?.clock_in && (
              <div className="text-sm text-gray-600">
                Clock In: <span className="font-semibold text-green-600">
                  {new Date(todayRecord.clock_in).toLocaleTimeString()}
                </span>
              </div>
            )}
            {todayRecord?.clock_out && (
              <div className="text-sm text-gray-600">
                Clock Out: <span className="font-semibold text-red-600">
                  {new Date(todayRecord.clock_out).toLocaleTimeString()}
                </span>
              </div>
            )}
            {todayRecord?.work_hours && (
              <div className="text-sm text-gray-600">
                Work Hours: <span className="font-semibold text-blue-600">
                  {todayRecord.work_hours} hours
                </span>
              </div>
            )}
          </div>

          <div className="space-x-3">
            {canClockIn && (
              <button
                onClick={handleClockIn}
                disabled={clockingIn}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition disabled:bg-gray-400 text-lg font-semibold"
              >
                {clockingIn ? "Processing..." : "Clock In"}
              </button>
            )}
            {canClockOut && (
              <button
                onClick={handleClockOut}
                disabled={clockingIn}
                className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg transition disabled:bg-gray-400 text-lg font-semibold"
              >
                {clockingIn ? "Processing..." : "Clock Out"}
              </button>
            )}
            {todayRecord?.clock_out && (
              <span className="inline-flex items-center px-4 py-3 bg-gray-100 text-gray-700 rounded-lg">
                ✓ Attendance Complete
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Records List */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Last 30 Days</h2>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading attendance records...</p>
          </div>
        ) : records.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500">No attendance records found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Clock In
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Clock Out
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Work Hours
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Notes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {records.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(record.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.clock_in
                        ? new Date(record.clock_in).toLocaleTimeString()
                        : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.clock_out
                        ? new Date(record.clock_out).toLocaleTimeString()
                        : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.work_hours ? `${record.work_hours}h` : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                          record.status
                        )}`}
                      >
                        {record.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {record.notes || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
