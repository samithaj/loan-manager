interface TimelineEvent {
  id: string;
  type: "PROCUREMENT" | "STOCK_ASSIGNMENT" | "TRANSFER" | "EXPENSE" | "REPAIR" | "SALE";
  title: string;
  description: string;
  date: string;
  user?: string;
  details?: Record<string, any>;
}

interface BikeLifecycleTimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export default function BikeLifecycleTimeline({
  events,
  className = ""
}: BikeLifecycleTimelineProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case "PROCUREMENT":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        );
      case "STOCK_ASSIGNMENT":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
          </svg>
        );
      case "TRANSFER":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
        );
      case "EXPENSE":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case "REPAIR":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      case "SALE":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case "PROCUREMENT":
        return "bg-green-100 text-green-800 border-green-200";
      case "STOCK_ASSIGNMENT":
        return "bg-gray-100 text-gray-800 border-gray-200";
      case "TRANSFER":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "EXPENSE":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "REPAIR":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "SALE":
        return "bg-teal-100 text-teal-800 border-teal-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Lifecycle Timeline</h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

        {/* Events */}
        <div className="space-y-6">
          {events.map((event, index) => (
            <div key={event.id} className="relative pl-14">
              {/* Icon */}
              <div
                className={`absolute left-0 w-12 h-12 rounded-full border-2 flex items-center justify-center ${getEventColor(
                  event.type
                )}`}
              >
                {getEventIcon(event.type)}
              </div>

              {/* Content */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-gray-900">{event.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                    {new Date(event.date).toLocaleDateString("en-LK", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit"
                    })}
                  </span>
                </div>

                {event.user && (
                  <p className="text-xs text-gray-500">By: {event.user}</p>
                )}

                {event.details && Object.keys(event.details).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <dl className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(event.details).map(([key, value]) => (
                        <div key={key}>
                          <dt className="text-gray-500 capitalize">
                            {key.replace(/_/g, " ")}:
                          </dt>
                          <dd className="text-gray-900 font-medium">
                            {typeof value === "number" && key.includes("price")
                              ? new Intl.NumberFormat("en-LK", {
                                  style: "currency",
                                  currency: "LKR"
                                }).format(value)
                              : String(value)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {events.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No lifecycle events yet</p>
        </div>
      )}
    </div>
  );
}
