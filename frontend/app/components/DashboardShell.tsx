"use client";

import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "firebase/auth";

import { firebaseAuthService } from "@/app/auth/firebaseConfig";
import type { SyncedUser } from "@/services/api";

export function DashboardShell({
  title,
  user,
  children,
}: {
  title: string;
  user: SyncedUser | null;
  children: ReactNode;
}) {
  const router = useRouter();

  const handleSignOut = async () => {
    try {
      await signOut(firebaseAuthService);
    } finally {
      localStorage.removeItem("userToken");
      localStorage.removeItem("userRole");
      router.replace("/auth");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold">{title}</h1>
            {user && (
              <p className="text-sm text-zinc-500">
                {user.fullName} · {user.email}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={handleSignOut}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">{children}</main>
    </div>
  );
}

export function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold">{title}</h2>
      {description && <p className="mt-1 text-sm text-zinc-500">{description}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-zinc-300 px-4 py-6 text-center text-sm text-zinc-500">
      {children}
    </p>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      {message}
    </div>
  );
}

export function LoadingState() {
  return <p className="py-10 text-center text-sm text-zinc-500">Loading your dashboard…</p>;
}