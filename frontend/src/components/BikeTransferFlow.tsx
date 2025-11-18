interface Transfer {
  id: string;
  bicycle_id: string;
  from_branch_id: string;
  to_branch_id: string;
  status: "PENDING" | "APPROVED" | "IN_TRANSIT" | "COMPLETED" | "REJECTED" | "CANCELLED";
  requested_by: string;
  requested_at: string;
  approved_by?: string;
  approved_at?: string;
  in_transit_at?: string;
  completed_by?: string;
  completed_at?: string;
  rejected_by?: string;
  rejected_at?: string;
  rejection_reason?: string;
  notes?: string;
}

interface BikeTransferFlowProps {
  transfer: Transfer;
  className?: string;
}

export default function BikeTransferFlow({ transfer, className = "" }: BikeTransferFlowProps) {
  const steps = [
    {
      key: "PENDING",
      label: "Pending",
      description: "Transfer requested",
      user: transfer.requested_by,
      date: transfer.requested_at,
      active: true
    },
    {
      key: "APPROVED",
      label: "Approved",
      description: "Transfer approved",
      user: transfer.approved_by,
      date: transfer.approved_at,
      active: ["APPROVED", "IN_TRANSIT", "COMPLETED"].includes(transfer.status)
    },
    {
      key: "IN_TRANSIT",
      label: "In Transit",
      description: "Bike being transferred",
      date: transfer.in_transit_at,
      active: ["IN_TRANSIT", "COMPLETED"].includes(transfer.status)
    },
    {
      key: "COMPLETED",
      label: "Completed",
      description: "Transfer completed",
      user: transfer.completed_by,
      date: transfer.completed_at,
      active: transfer.status === "COMPLETED"
    }
  ];

  const isRejected = transfer.status === "REJECTED";
  const isCancelled = transfer.status === "CANCELLED";

  const getStatusColor = () => {
    switch (transfer.status) {
      case "PENDING":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "APPROVED":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "IN_TRANSIT":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "COMPLETED":
        return "bg-green-100 text-green-800 border-green-300";
      case "REJECTED":
        return "bg-red-100 text-red-800 border-red-300";
      case "CANCELLED":
        return "bg-gray-100 text-gray-800 border-gray-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Transfer Status</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor()}`}>
          {transfer.status.replace(/_/g, " ")}
        </span>
      </div>

      {/* Transfer Route */}
      <div className="mb-8 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">From</div>
            <div className="font-semibold text-gray-900">{transfer.from_branch_id}</div>
          </div>
          <div className="flex-1 mx-4">
            <svg
              className="w-full h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 100 24"
              preserveAspectRatio="none"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M0 12 L100 12"
                markerEnd="url(#arrowhead)"
              />
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="10"
                  refX="9"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill="currentColor" />
                </marker>
              </defs>
            </svg>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">To</div>
            <div className="font-semibold text-gray-900">{transfer.to_branch_id}</div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {!isRejected && !isCancelled && (
        <div className="relative">
          <div className="flex items-center justify-between mb-8">
            {steps.map((step, index) => (
              <div key={step.key} className="flex-1 relative">
                <div className="flex flex-col items-center">
                  {/* Circle */}
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                      step.active
                        ? "bg-blue-600 border-blue-600 text-white"
                        : "bg-white border-gray-300 text-gray-400"
                    }`}
                  >
                    {step.active ? (
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <span className="text-sm font-semibold">{index + 1}</span>
                    )}
                  </div>

                  {/* Line */}
                  {index < steps.length - 1 && (
                    <div
                      className={`absolute top-5 left-1/2 w-full h-0.5 -z-10 ${
                        steps[index + 1].active ? "bg-blue-600" : "bg-gray-300"
                      }`}
                      style={{ width: "calc(100% - 2.5rem)" }}
                    />
                  )}

                  {/* Label */}
                  <div className="mt-3 text-center">
                    <div className={`text-sm font-medium ${step.active ? "text-gray-900" : "text-gray-500"}`}>
                      {step.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{step.description}</div>
                    {step.date && (
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(step.date).toLocaleDateString("en-LK", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </div>
                    )}
                    {step.user && (
                      <div className="text-xs text-gray-500 mt-0.5">by {step.user}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rejection Info */}
      {isRejected && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-red-600 mr-3 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900 mb-1">Transfer Rejected</h4>
              {transfer.rejection_reason && (
                <p className="text-sm text-red-700">{transfer.rejection_reason}</p>
              )}
              {transfer.rejected_by && transfer.rejected_at && (
                <p className="text-xs text-red-600 mt-2">
                  Rejected by {transfer.rejected_by} on{" "}
                  {new Date(transfer.rejected_at).toLocaleString("en-LK")}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cancellation Info */}
      {isCancelled && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-gray-600 mr-3 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 mb-1">Transfer Cancelled</h4>
              <p className="text-sm text-gray-600">This transfer request was cancelled.</p>
            </div>
          </div>
        </div>
      )}

      {/* Notes */}
      {transfer.notes && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-1">Notes</h4>
          <p className="text-sm text-blue-700">{transfer.notes}</p>
        </div>
      )}
    </div>
  );
}
