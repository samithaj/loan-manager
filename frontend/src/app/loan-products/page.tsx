import RoleGuard from "@/components/RoleGuard";
import LoanProductManager from "@/components/LoanProductManager";

export default function Page() {
  return (
    <main className="min-h-screen p-8 space-y-6">
      <RoleGuard requiredRoles={["user", "admin"]}>
        <LoanProductManager />
      </RoleGuard>
    </main>
  );
}


