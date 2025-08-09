"use client";
import { useEffect, useState } from "react";

type RoleGuardProps = {
  requiredRoles: string[];
  children: React.ReactNode;
};

type Me = { username: string; roles: string[] };

// Cookie-based auth: no headers needed; include credentials in fetch

export default function RoleGuard({ requiredRoles, children }: RoleGuardProps) {
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const refetch = async () => {
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
        const res = await fetch(`${base}/v1/me`, { cache: "no-store", credentials: "include" });
        if (res.status === 401) {
          if (!cancelled) {
            setError("Not authorized");
            setAllowed(false);
          }
          window.location.href = "/login";
          return;
        }
        if (!res.ok) {
          if (!cancelled) {
            setError(`Access check failed (${res.status})`);
            setAllowed(false);
          }
          return;
        }
        const data = (await res.json()) as Me;
        const roles = Array.isArray(data.roles) ? data.roles : [];
        const isAllowed = requiredRoles.length === 0 || requiredRoles.some((r) => roles.includes(r));
        if (!cancelled) {
          if (!isAllowed) setError("Insufficient role");
          setAllowed(isAllowed);
        }
      } catch {
        if (!cancelled) {
          setError("Not authorized");
          setAllowed(false);
        }
      }
    };
    refetch();
    const onAuth = () => refetch();
    window.addEventListener("auth:updated", onAuth);
    return () => {
      cancelled = true;
      window.removeEventListener("auth:updated", onAuth);
    };
  }, [requiredRoles]);

  if (allowed === null) return <div className="text-sm text-gray-500">Checking access…</div>;
  if (!allowed) return <div className="text-sm text-red-600">{error || "Insufficient role"}</div>;
  return <>{children}</>;
}


