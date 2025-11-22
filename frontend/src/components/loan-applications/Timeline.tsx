interface TimelineEvent {
  timestamp: string;
  event_type: string;
  actor?: string;
  description: string;
  details?: any;
}

interface TimelineProps {
  events: TimelineEvent[];
}

export default function Timeline({ events }: TimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No timeline events yet
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {events.map((event, index) => (
        <div key={index} className="flex gap-4">
          {/* Timeline line */}
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 bg-blue-600 rounded-full" />
            {index < events.length - 1 && (
              <div className="w-0.5 flex-1 bg-blue-200 my-1" style={{ minHeight: "20px" }} />
            )}
          </div>

          {/* Event content */}
          <div className="flex-1 pb-6">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-medium text-gray-900">
                  {event.description}
                </div>
                {event.actor && (
                  <div className="text-sm text-gray-600 mt-1">
                    by {event.actor}
                  </div>
                )}
                {event.details && Object.keys(event.details).length > 0 && (
                  <div className="mt-2 text-sm bg-gray-50 rounded p-2">
                    {Object.entries(event.details).map(([key, value]) => (
                      <div key={key} className="text-gray-700">
                        <span className="font-medium">{key}:</span>{" "}
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-sm text-gray-500 whitespace-nowrap ml-4">
                {new Date(event.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
