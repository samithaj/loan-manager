"use client";
import { useMemo, useState } from "react";

export type Column<T> = {
  key: keyof T;
  header: string;
  render?: (row: T) => React.ReactNode;
};

type SortDir = "asc" | "desc";

export function PagedTable<T extends Record<string, unknown>>({
  rows,
  columns,
  initialSort,
  pageSize = 10,
}: {
  rows: T[];
  columns: Column<T>[];
  initialSort?: { key: keyof T; dir: SortDir };
  pageSize?: number;
}) {
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<keyof T | undefined>(initialSort?.key);
  const [sortDir, setSortDir] = useState<SortDir>(initialSort?.dir || "asc");

  const sorted = useMemo(() => {
    if (!sortKey) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return -1;
      if (bv == null) return 1;
      const as = String(av);
      const bs = String(bv);
      if (as < bs) return sortDir === "asc" ? -1 : 1;
      if (as > bs) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const pageSafe = Math.min(page, totalPages);
  const start = (pageSafe - 1) * pageSize;
  const paged = sorted.slice(start, start + pageSize);

  function onSort(key: keyof T) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
    setPage(1);
  }

  return (
    <div className="space-y-3">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={`col-${String(c.header)}`}
                className="text-left border-b py-2 cursor-pointer select-none"
                onClick={() => onSort(c.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {c.header}
                  {sortKey === c.key && (
                    <span className="text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paged.map((row, idx) => (
            <tr key={idx} className="border-b last:border-0">
              {columns.map((c) => (
                <td key={`row-${idx}-col-${String(c.header)}`} className="py-2 pr-3">
                  {c.render ? c.render(row) : String(row[c.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
          {paged.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="py-6 text-center text-gray-500">
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="flex items-center justify-between text-sm">
        <div>
          Page {pageSafe} of {totalPages}
        </div>
        <div className="space-x-2">
          <button
            className="border rounded px-2 py-1 disabled:opacity-50"
            disabled={pageSafe <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>
          <button
            className="border rounded px-2 py-1 disabled:opacity-50"
            disabled={pageSafe >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}



