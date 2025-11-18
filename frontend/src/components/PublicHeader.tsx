"use client";
import Link from "next/link";
import { useState } from "react";

export default function PublicHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="w-full border-b bg-white shadow-sm sticky top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/bicycles" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-gray-900">Bicycle Hire</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/bicycles" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
              Browse Bicycles
            </Link>
            <Link href="/bicycles/apply" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
              Apply Now
            </Link>
            <Link href="/bicycles/branches" className="text-gray-700 hover:text-blue-600 font-medium transition-colors">
              Branches
            </Link>
            <Link
              href="/login"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Staff Login
            </Link>
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-gray-700 hover:bg-gray-100"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <nav className="flex flex-col gap-4">
              <Link
                href="/bicycles"
                className="text-gray-700 hover:text-blue-600 font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                Browse Bicycles
              </Link>
              <Link
                href="/bicycles/apply"
                className="text-gray-700 hover:text-blue-600 font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                Apply Now
              </Link>
              <Link
                href="/bicycles/branches"
                className="text-gray-700 hover:text-blue-600 font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                Branches
              </Link>
              <Link
                href="/login"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-center font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                Staff Login
              </Link>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
