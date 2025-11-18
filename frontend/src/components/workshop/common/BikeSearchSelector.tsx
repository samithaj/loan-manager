"use client";
import { useState, useEffect, useRef } from "react";

interface Bike {
  id: number;
  license_plate: string;
  frame_number: string;
  title?: string;
  model?: string;
  make?: string;
  year?: number;
  odometer?: number;
  status?: string;
  photo_url?: string;
}

interface BikeSearchSelectorProps {
  onSelect: (bike: Bike) => void;
  label?: string;
  placeholder?: string;
  branchId?: number;
  required?: boolean;
}

export default function BikeSearchSelector({
  onSelect,
  label = "Search Bike",
  placeholder = "Type license plate or frame number...",
  branchId,
  required = false,
}: BikeSearchSelectorProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Bike[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedBike, setSelectedBike] = useState<Bike | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          search: query,
          limit: "10",
          ...(branchId && { branch_id: branchId.toString() }),
        });
        const res = await fetch(`${base}/v1/bicycles?${params}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setResults(data.bicycles || data);
          setIsOpen(true);
        }
      } catch (error) {
        console.error("Failed to search bikes:", error);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, branchId]);

  const handleSelect = (bike: Bike) => {
    setSelectedBike(bike);
    onSelect(bike);
    setQuery("");
    setResults([]);
    setIsOpen(false);
  };

  const handleClear = () => {
    setSelectedBike(null);
    setQuery("");
  };

  return (
    <div ref={wrapperRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {selectedBike ? (
        <div className="border border-gray-300 rounded-lg p-3 bg-gray-50">
          <div className="flex items-center gap-3">
            {selectedBike.photo_url && (
              <img
                src={selectedBike.photo_url}
                alt={selectedBike.title || "Bike"}
                className="w-16 h-16 object-cover rounded"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900">
                {selectedBike.title || `${selectedBike.make} ${selectedBike.model}`}
              </div>
              <div className="text-sm text-gray-600">
                License: {selectedBike.license_plate} • Frame: {selectedBike.frame_number}
              </div>
              {selectedBike.odometer && (
                <div className="text-xs text-gray-500">
                  Odometer: {selectedBike.odometer.toLocaleString()} km
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      ) : (
        <>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results.length > 0 && setIsOpen(true)}
            placeholder={placeholder}
            required={required}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {loading && (
            <div className="absolute right-3 top-9 text-gray-400">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          )}
        </>
      )}

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {results.map((bike) => (
            <button
              key={bike.id}
              type="button"
              onClick={() => handleSelect(bike)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
            >
              <div className="flex items-center gap-3">
                {bike.photo_url && (
                  <img
                    src={bike.photo_url}
                    alt={bike.title || "Bike"}
                    className="w-12 h-12 object-cover rounded"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900">
                    {bike.title || `${bike.make} ${bike.model} (${bike.year})`}
                  </div>
                  <div className="text-sm text-gray-600">
                    License: {bike.license_plate} • Frame: {bike.frame_number}
                  </div>
                  {bike.odometer && (
                    <div className="text-xs text-gray-500">
                      Odometer: {bike.odometer.toLocaleString()} km
                    </div>
                  )}
                </div>
                {bike.status && (
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                    {bike.status}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
      {isOpen && results.length === 0 && query.length >= 2 && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-4 text-center text-gray-500">
          No bikes found for "{query}"
        </div>
      )}
    </div>
  );
}
