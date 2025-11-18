interface BikeCostSummaryProps {
  costSummary: {
    bicycle_id: string;
    stock_number?: string;
    base_purchase_price: number;
    total_repair_cost: number;
    total_branch_expenses: number;
    total_cost: number;
    selling_price?: number;
    profit_or_loss?: number;
    repair_jobs?: {
      job_id: string;
      description: string;
      total_cost: number;
      completed_date?: string;
    }[];
    branch_expenses?: {
      expense_id: string;
      category: string;
      amount: number;
      expense_date: string;
      notes?: string;
    }[];
  };
  className?: string;
}

export default function BikeCostSummary({ costSummary, className = "" }: BikeCostSummaryProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-LK", {
      style: "currency",
      currency: "LKR",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const profitColor = costSummary.profit_or_loss
    ? costSummary.profit_or_loss > 0
      ? "text-green-600"
      : costSummary.profit_or_loss < 0
      ? "text-red-600"
      : "text-gray-600"
    : "text-gray-400";

  return (
    <div className={`bg-white rounded-lg shadow-md overflow-hidden ${className}`}>
      <div className="bg-gray-50 px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Cost Summary</h3>
        {costSummary.stock_number && (
          <p className="text-sm text-gray-600 font-mono">{costSummary.stock_number}</p>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Main Cost Breakdown */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Base Purchase Price</span>
            <span className="text-sm font-medium">
              {formatCurrency(costSummary.base_purchase_price)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total Repair Cost</span>
            <span className="text-sm font-medium">
              {formatCurrency(costSummary.total_repair_cost)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total Branch Expenses</span>
            <span className="text-sm font-medium">
              {formatCurrency(costSummary.total_branch_expenses)}
            </span>
          </div>

          <div className="pt-3 border-t flex justify-between items-center">
            <span className="font-semibold text-gray-900">Total Cost</span>
            <span className="font-bold text-lg">
              {formatCurrency(costSummary.total_cost)}
            </span>
          </div>
        </div>

        {/* Selling Price & P/L */}
        {costSummary.selling_price !== null && costSummary.selling_price !== undefined && (
          <div className="pt-4 border-t space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Selling Price</span>
              <span className="text-sm font-medium">
                {formatCurrency(costSummary.selling_price)}
              </span>
            </div>

            {costSummary.profit_or_loss !== null && costSummary.profit_or_loss !== undefined && (
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="font-semibold text-gray-900">Profit / Loss</span>
                <span className={`font-bold text-xl ${profitColor}`}>
                  {formatCurrency(costSummary.profit_or_loss)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Repair Jobs Detail */}
        {costSummary.repair_jobs && costSummary.repair_jobs.length > 0 && (
          <div className="pt-4 border-t">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Repair Jobs</h4>
            <div className="space-y-2">
              {costSummary.repair_jobs.map((job) => (
                <div key={job.job_id} className="flex justify-between items-start text-sm">
                  <div className="flex-1">
                    <p className="text-gray-700">{job.description}</p>
                    {job.completed_date && (
                      <p className="text-xs text-gray-500">
                        {new Date(job.completed_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <span className="text-gray-900 font-medium ml-4">
                    {formatCurrency(job.total_cost)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Branch Expenses Detail */}
        {costSummary.branch_expenses && costSummary.branch_expenses.length > 0 && (
          <div className="pt-4 border-t">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Branch Expenses</h4>
            <div className="space-y-2">
              {costSummary.branch_expenses.map((expense) => (
                <div key={expense.expense_id} className="flex justify-between items-start text-sm">
                  <div className="flex-1">
                    <p className="text-gray-700">
                      <span className="font-medium">{expense.category}</span>
                      {expense.notes && ` - ${expense.notes}`}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(expense.expense_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="text-gray-900 font-medium ml-4">
                    {formatCurrency(expense.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
