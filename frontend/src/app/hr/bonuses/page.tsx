"use client";

import { useState, useEffect } from "react";

interface BonusPayment {
  id: string;
  user_id: string;
  bonus_rule_id?: string;
  period_start: string;
  period_end: string;
  target_amount?: number;
  actual_amount?: number;
  achievement_percentage?: number;
  bonus_amount: number;
  calculation_details?: any;
  status: string;
  approved_by?: string;
  approved_at?: string;
  paid_at?: string;
  payment_reference?: string;
  notes?: string;
  created_at: string;
}

interface PerformanceMetric {
  id: string;
  user_id: string;
  period_start: string;
  period_end: string;
  actual_loans: number;
  actual_loan_amount: number;
  actual_bicycles: number;
  actual_bicycle_revenue: number;
  achievement_percentage: number;
  calculated_at: string;
}

export default function BonusesPage() {
  const [payments, setPayments] = useState<BonusPayment[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"payments" | "performance">("payments");

  useEffect(() => {
    if (activeTab === "payments") {
      fetchPayments();
    } else {
      fetchMetrics();
    }
  }, [activeTab]);

  const fetchPayments = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/bonuses/payments?limit=50`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setPayments(data.items || []);
      }
    } catch (error) {
      console.error("Error fetching bonus payments:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/v1/bonuses/metrics`,
        { credentials: "include" }
      );

      if (response.ok) {
        const data = await response.json();
        setMetrics(data || []);
      }
    } catch (error) {
      console.error("Error fetching performance metrics:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING":
        return "bg-yellow-100 text-yellow-800";
      case "APPROVED":
        return "bg-blue-100 text-blue-800";
      case "PAID":
        return "bg-green-100 text-green-800";
      case "REJECTED":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD"
    }).format(amount);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Bonus & Performance</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab("payments")}
            className={`${
              activeTab === "payments"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Bonus Payments
          </button>
          <button
            onClick={() => setActiveTab("performance")}
            className={`${
              activeTab === "performance"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Performance Metrics
          </button>
        </nav>
      </div>

      {/* Bonus Payments Tab */}
      {activeTab === "payments" && (
        <div>
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading bonus payments...</p>
            </div>
          ) : payments.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500">No bonus payments found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {payments.map((payment) => (
                <div
                  key={payment.id}
                  className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {formatCurrency(payment.bonus_amount)}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Period: {new Date(payment.period_start).toLocaleDateString()} -{" "}
                        {new Date(payment.period_end).toLocaleDateString()}
                      </p>
                    </div>
                    <span
                      className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(
                        payment.status
                      )}`}
                    >
                      {payment.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    {payment.target_amount && (
                      <div>
                        <div className="text-xs text-gray-500">Target</div>
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(payment.target_amount)}
                        </div>
                      </div>
                    )}
                    {payment.actual_amount && (
                      <div>
                        <div className="text-xs text-gray-500">Actual</div>
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(payment.actual_amount)}
                        </div>
                      </div>
                    )}
                    {payment.achievement_percentage && (
                      <div>
                        <div className="text-xs text-gray-500">Achievement</div>
                        <div className="text-sm font-semibold text-blue-600">
                          {payment.achievement_percentage.toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>

                  {payment.calculation_details?.rules_applied && (
                    <div className="bg-gray-50 rounded p-3 mb-3">
                      <div className="text-xs font-semibold text-gray-700 mb-2">
                        Calculation Details:
                      </div>
                      <div className="space-y-1">
                        {payment.calculation_details.rules_applied.map(
                          (rule: any, idx: number) => (
                            <div key={idx} className="text-xs text-gray-600">
                              • {rule.rule_name} ({rule.rule_type}):{" "}
                              {formatCurrency(rule.bonus_amount)}
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {payment.notes && (
                    <div className="text-sm text-gray-600 border-t pt-3">
                      <span className="font-medium">Notes:</span> {payment.notes}
                    </div>
                  )}

                  {payment.payment_reference && (
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Reference:</span>{" "}
                      {payment.payment_reference}
                    </div>
                  )}

                  <div className="flex justify-between items-center mt-4 pt-3 border-t text-xs text-gray-500">
                    <div>Submitted: {new Date(payment.created_at).toLocaleDateString()}</div>
                    {payment.paid_at && (
                      <div className="text-green-600 font-medium">
                        Paid: {new Date(payment.paid_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Summary */}
          {payments.length > 0 && (
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {payments.length}
                  </div>
                  <div className="text-sm text-gray-500">Total Payments</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(
                      payments.reduce((sum, p) => sum + p.bonus_amount, 0)
                    )}
                  </div>
                  <div className="text-sm text-gray-500">Total Amount</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {payments.filter((p) => p.status === "PENDING").length}
                  </div>
                  <div className="text-sm text-gray-500">Pending</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {payments.filter((p) => p.status === "PAID").length}
                  </div>
                  <div className="text-sm text-gray-500">Paid</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Performance Metrics Tab */}
      {activeTab === "performance" && (
        <div>
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading performance metrics...</p>
            </div>
          ) : metrics.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500">No performance metrics found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {metrics.map((metric) => (
                <div
                  key={metric.id}
                  className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Achievement: {metric.achievement_percentage.toFixed(1)}%
                      </h3>
                      <p className="text-sm text-gray-600">
                        Period: {new Date(metric.period_start).toLocaleDateString()} -{" "}
                        {new Date(metric.period_end).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Calculated</div>
                      <div className="text-sm text-gray-700">
                        {new Date(metric.calculated_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-gray-500">Bicycles Sold</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {metric.actual_bicycles}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Bicycle Revenue</div>
                      <div className="text-lg font-semibold text-blue-600">
                        {formatCurrency(metric.actual_bicycle_revenue)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Loans Processed</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {metric.actual_loans}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Loan Amount</div>
                      <div className="text-lg font-semibold text-blue-600">
                        {formatCurrency(metric.actual_loan_amount)}
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex mb-2 items-center justify-between">
                      <div className="text-xs font-semibold text-gray-700">
                        Achievement Progress
                      </div>
                      <div className="text-xs font-semibold text-gray-700">
                        {metric.achievement_percentage.toFixed(1)}%
                      </div>
                    </div>
                    <div className="overflow-hidden h-3 text-xs flex rounded bg-gray-200">
                      <div
                        style={{
                          width: `${Math.min(metric.achievement_percentage, 100)}%`
                        }}
                        className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${
                          metric.achievement_percentage >= 100
                            ? "bg-green-500"
                            : metric.achievement_percentage >= 80
                            ? "bg-yellow-500"
                            : "bg-blue-500"
                        }`}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
