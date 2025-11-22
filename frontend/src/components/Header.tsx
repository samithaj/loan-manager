"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

type Me = { username: string; roles: string[] };

export default function Header() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [workshopOpen, setWorkshopOpen] = useState(false);
  const [bikesOpen, setBikesOpen] = useState(false);
  const [loanAppsOpen, setLoanAppsOpen] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`${base}/v1/me`, { credentials: "include", cache: "no-store" });
      if (res.ok) {
        const data = (await res.json()) as Me;
        setMe(data);
      } else {
        setMe(null);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const onAuth = () => load();
    window.addEventListener("auth:updated", onAuth);
    return () => window.removeEventListener("auth:updated", onAuth);
  }, []);

  async function onLogout() {
    await fetch(`${base}/v1/auth/logout`, { method: "POST", credentials: "include" });
    setMe(null);
    window.dispatchEvent(new Event("auth:updated"));
    location.href = "/login";
  }

  return (
    <header className="w-full border-b border-gray-800 bg-black/40 text-sm">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="font-semibold text-white">Loan Manager</Link>
          {me && (
            <nav className="flex items-center gap-3 text-blue-400">
              <Link href="/reference">Reference data</Link>
              <Link href="/loan-products">Loan products</Link>
              <Link href="/clients">Clients</Link>
              <Link href="/inventory">Inventory</Link>

              {/* Bikes Dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setBikesOpen(true)}
                onMouseLeave={() => setBikesOpen(false)}
              >
                <button className="flex items-center gap-1 hover:text-blue-300 transition-colors">
                  Bikes
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                {bikesOpen && (
                  <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg py-2 min-w-[200px] z-50">
                    <Link href="/bikes" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      All Bikes
                    </Link>
                    <Link href="/bikes/inventory" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Inventory
                    </Link>
                    <Link href="/bikes/acquisition" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Acquisition
                    </Link>
                    <Link href="/bikes/sales" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Sales
                    </Link>
                    <Link href="/bikes/transfers" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Transfers
                    </Link>
                  </div>
                )}
              </div>

              {/* Workshop Dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setWorkshopOpen(true)}
                onMouseLeave={() => setWorkshopOpen(false)}
              >
                <button className="flex items-center gap-1 hover:text-blue-300 transition-colors">
                  Workshop
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                {workshopOpen && (
                  <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg py-2 min-w-[200px] z-50">
                    <Link href="/workshop" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Dashboard
                    </Link>
                    <Link href="/workshop/parts" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Parts Inventory
                    </Link>
                    <Link href="/workshop/stock-batches" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Stock Batches
                    </Link>
                    <Link href="/workshop/jobs" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Repair Jobs
                    </Link>
                    <Link href="/workshop/markup-rules" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Markup Rules
                    </Link>
                    <Link href="/workshop/reports" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Reports
                    </Link>
                  </div>
                )}
              </div>

              {/* Loan Applications Dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setLoanAppsOpen(true)}
                onMouseLeave={() => setLoanAppsOpen(false)}
              >
                <button className="flex items-center gap-1 hover:text-blue-300 transition-colors">
                  Loan Applications
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                {loanAppsOpen && (
                  <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg py-2 min-w-[200px] z-50">
                    <Link href="/loan-applications" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      My Applications
                    </Link>
                    <Link href="/loan-applications/new" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      New Application
                    </Link>
                    <Link href="/loan-applications/queue" className="block px-4 py-2 hover:bg-gray-800 transition-colors">
                      Approval Queue
                    </Link>
                  </div>
                )}
              </div>

              <Link href="/applications">Applications</Link>
            </nav>
          )}
        </div>
        <div className="flex items-center gap-3">
          {loading ? (
            <span className="text-gray-400">…</span>
          ) : me ? (
            <>
              <Link href="/profile" className="text-gray-200 underline">{me.username}</Link>
              <button onClick={onLogout} className="border rounded px-2 py-1">Logout</button>
            </>
          ) : (
            <Link href="/login" className="text-blue-400 underline">Login</Link>
          )}
        </div>
      </div>
    </header>
  );
}


