import type { Branch } from "@/types/bicycle";

async function getBranches(): Promise<Branch[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${baseUrl}/public/branches`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || [];
  } catch (error) {
    console.error("Failed to fetch branches:", error);
    return [];
  }
}

export default async function BranchesPage() {
  const branches = await getBranches();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Our Branches</h1>
          <p className="text-gray-600">
            Find a branch near you. Visit us to view bicycles and get personalized assistance.
          </p>
        </div>
      </div>

      {/* Branches Grid */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {branches.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-500 text-lg">No branches found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {branches
              .filter((branch) => branch.allows_bicycle_sales)
              .sort((a, b) => a.bicycle_display_order - b.bicycle_display_order)
              .map((branch) => (
                <div
                  key={branch.id}
                  className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {/* Map Placeholder */}
                  {branch.map_coordinates ? (
                    <div className="h-48 bg-gray-200 relative">
                      <div className="absolute inset-0 flex items-center justify-center">
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${branch.map_coordinates.lat},${branch.map_coordinates.lng}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          View on Map
                        </a>
                      </div>
                    </div>
                  ) : (
                    <div className="h-48 bg-gradient-to-br from-blue-500 to-blue-600" />
                  )}

                  <div className="p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-2">{branch.name}</h2>

                    {branch.public_description && (
                      <p className="text-sm text-gray-600 mb-4">{branch.public_description}</p>
                    )}

                    <div className="space-y-3 text-sm">
                      {/* Operating Hours */}
                      {branch.operating_hours && (
                        <div className="flex items-start gap-2">
                          <svg
                            className="w-5 h-5 text-gray-500 mt-0.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <div>
                            <div className="font-medium text-gray-900">Operating Hours</div>
                            <div className="text-gray-600 whitespace-pre-line">
                              {branch.operating_hours}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Location */}
                      {branch.map_coordinates && (
                        <div className="flex items-start gap-2">
                          <svg
                            className="w-5 h-5 text-gray-500 mt-0.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          <div>
                            <div className="font-medium text-gray-900">Location</div>
                            <a
                              href={`https://www.google.com/maps/search/?api=1&query=${branch.map_coordinates.lat},${branch.map_coordinates.lng}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 underline"
                            >
                              {branch.map_coordinates.lat.toFixed(6)}, {branch.map_coordinates.lng.toFixed(6)}
                            </a>
                          </div>
                        </div>
                      )}

                      {/* Contact */}
                      <div className="flex items-start gap-2">
                        <svg
                          className="w-5 h-5 text-gray-500 mt-0.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                          />
                        </svg>
                        <div>
                          <div className="font-medium text-gray-900">Contact</div>
                          <div className="text-gray-600">Call for more information</div>
                        </div>
                      </div>
                    </div>

                    {/* View Bicycles Button */}
                    <a
                      href={`/bicycles/catalog?branch=${branch.id}`}
                      className="mt-6 block w-full bg-blue-600 text-white text-center py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      View Bicycles at This Branch
                    </a>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
