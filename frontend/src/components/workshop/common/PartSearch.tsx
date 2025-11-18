"use client";
import { useState, useEffect, useRef } from "react";
import CategoryBadge, { PartCategory } from "./CategoryBadge";

interface Part {
  id: number;
  part_code: string;
  name: string;
  category: PartCategory;
  unit: string;
  available_quantity?: number;
  average_cost?: number;
}

interface PartSearchProps {
  onSelect: (part: Part) => void;
  label?: string;
  placeholder?: string;
  branchId?: number;
  excludeIds?: number[];
  required?: boolean;
}

export default function PartSearch({
  onSelect,
  label = "Search Part",
  placeholder = "Type part code or name...",
  branchId,
  excludeIds = [],
  required = false,
}: PartSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Part[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
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
          active_only: "true",
          ...(branchId && { branch_id: branchId.toString() }),
        });
        const res = await fetch(`${base}/v1/workshop/parts?${params}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          const filteredData = data.filter((p: Part) => !excludeIds.includes(p.id));
          setResults(filteredData.slice(0, 10)); // Limit to 10 results
          setIsOpen(true);
        }
      } catch (error) {
        console.error("Failed to search parts:", error);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, branchId, excludeIds.join(",")]);

  const handleSelect = (part: Part) => {
    onSelect(part);
    setQuery("");
    setResults([]);
    setIsOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
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
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {results.map((part) => (
            <button
              key={part.id}
              type="button"
              onClick={() => handleSelect(part)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900">{part.part_code}</span>
                    <CategoryBadge category={part.category} size="sm" />
                  </div>
                  <div className="text-sm text-gray-700">{part.name}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Unit: {part.unit}
                    {part.available_quantity !== undefined && (
                      <span className={`ml-2 ${part.available_quantity > 0 ? "text-green-600" : "text-red-600"}`}>
                        • {part.available_quantity} available
                      </span>
                    )}
                  </div>
                </div>
                {part.average_cost !== undefined && (
                  <div className="text-sm text-gray-600">
                    ${part.average_cost.toFixed(2)}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
      {isOpen && results.length === 0 && query.length >= 2 && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-4 text-center text-gray-500">
          No parts found for "{query}"
        </div>
      )}
    </div>
  );
}
