"use client";

import {
  DashboardShell,
  EmptyState,
  ErrorBanner,
  LoadingState,
  Panel,
  StatCard,
} from "@/app/components/DashboardShell";
import { formatDate } from "@/lib/format";
import { useDashboard } from "@/lib/useDashboard";
import { fetchStudentDashboard, type AssignmentStatus } from "@/services/dashboardApi";

const statusStyles: Record<AssignmentStatus, string> = {
  open: "bg-blue-50 text-blue-700",
  completed: "bg-green-50 text-green-700",
  overdue: "bg-red-50 text-red-700",
};

const statusLabels: Record<AssignmentStatus, string> = {
  open: "Open",
  completed: "Completed",
  overdue: "Overdue",
};

function masteryBarColor(percent: number): string {
  if (percent >= 70) return "bg-emerald-500";
  if (percent >= 40) return "bg-amber-500";
  return "bg-rose-500";
}

export default function StudentDashboardPage() {
  // A teacher who opens / gets a 403 and is sent to their own dashboard.
  const { data, error, loading } = useDashboard(fetchStudentDashboard, "/teacher");

  return (
    <DashboardShell title="Student dashboard" user={data?.profile ?? null}>
      <ErrorBanner message={error} />
      {loading && <LoadingState />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Open assignments" value={data.stats.openAssignments} />
            <StatCard label="Completed" value={data.stats.completedAssignments} />
            <StatCard
              label="Average score"
              value={
                data.stats.averageScorePercent === null
                  ? "—"
                  : `${data.stats.averageScorePercent}%`
              }
            />
            <StatCard label="Concepts tracked" value={data.stats.conceptsTracked} />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Panel
                title="Assigned homework"
                description="Soonest due date first."
              >
                {data.assignments.length === 0 ? (
                  <EmptyState>Nothing has been assigned yet.</EmptyState>
                ) : (
                  <ul className="divide-y divide-zinc-100">
                    {data.assignments.map((a) => (
                      <li
                        key={a.id}
                        className="flex flex-wrap items-center justify-between gap-3 py-3"
                      >
                        <div>
                          <p className="font-medium">{a.title}</p>
                          <p className="text-xs text-zinc-500">
                            {a.materialTitle} · {a.teacherName} · due {formatDate(a.dueDate)}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          {a.bestScorePercent !== null && (
                            <span className="text-sm text-zinc-600">
                              Best: {a.bestScorePercent}%
                            </span>
                          )}
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[a.status]}`}
                          >
                            {statusLabels[a.status]}
                          </span>
                          {a.status !== "completed" && (
                            <button
                              type="button"
                              disabled
                              title="The quiz screen is coming in the next feature."
                              className="rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-400"
                            >
                              Start
                            </button>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </div>

            <Panel
              title="Concept mastery"
              description="Weakest concepts first."
            >
              {data.mastery.length === 0 ? (
                <EmptyState>
                  Your mastery appears here once you start answering questions.
                </EmptyState>
              ) : (
                <ul className="space-y-4">
                  {data.mastery.map((m) => (
                    <li key={m.conceptTag}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="font-medium">{m.conceptTag}</span>
                        <span className="text-zinc-500">{m.masteryPercent}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
                        <div
                          className={`h-full rounded-full ${masteryBarColor(m.masteryPercent)}`}
                          style={{ width: `${m.masteryPercent}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>

          <Panel title="Recent attempts">
            {data.recentAttempts.length === 0 ? (
              <EmptyState>No attempts yet.</EmptyState>
            ) : (
              <ul className="divide-y divide-zinc-100">
                {data.recentAttempts.map((a) => (
                  <li key={a.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="font-medium">{a.assignmentTitle}</p>
                      <p className="text-xs text-zinc-500">{formatDate(a.attemptedAt)}</p>
                    </div>
                    <span className="text-sm font-medium">{a.scorePercent}%</span>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </>
      )}
    </DashboardShell>
  );
}