"use client";

import Link from "next/link";
import { useState } from "react";

import {
  DashboardShell,
  EmptyState,
  ErrorBanner,
  LoadingState,
  Panel,
  StatCard,
} from "@/app/components/DashboardShell";
import { formatDate, todayLocalIso } from "@/lib/format";
import { useDashboard } from "@/lib/useDashboard";
import {
  assignHomework,
  fetchTeacherDashboard,
  uploadMaterial,
  type TeacherDashboardData,
} from "@/services/dashboardApi";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500";
const buttonClass =
  "rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50";

function UploadForm({ onDone }: { onDone: () => void }) {
  const [title, setTitle] = useState("");
  const [textBody, setTextBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const result = await uploadMaterial({ title: title.trim(), textBody });
      setSuccess(`"${result.title}" saved (${result.chunksIndexed} chunks indexed).`);
      setTitle("");
      setTextBody("");
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <ErrorBanner message={error} />
      {success && (
        <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </p>
      )}
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="material-title">
          Title
        </label>
        <input
          id="material-title"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Photosynthesis – Chapter 4"
          className={inputClass}
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="material-text">
          Study notes
        </label>
        <textarea
          id="material-text"
          required
          rows={7}
          value={textBody}
          onChange={(e) => setTextBody(e.target.value)}
          placeholder="Paste the lesson text here. It is split into chunks and indexed for question generation."
          className={inputClass}
        />
      </div>
      <button type="submit" disabled={busy || !title.trim() || !textBody.trim()} className={buttonClass}>
        {busy ? "Uploading…" : "Upload material"}
      </button>
    </form>
  );
}

function AssignForm({
  materials,
  onDone,
}: {
  materials: TeacherDashboardData["materials"];
  onDone: () => void;
}) {
  const [materialId, setMaterialId] = useState("");
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [today] = useState(todayLocalIso);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  if (materials.length === 0) {
    return <EmptyState>Upload a study material first, then you can assign it.</EmptyState>;
  }

  // Default to the first material until the teacher picks one.
  const selectedId = materialId || String(materials[0].id);
  const selectedMaterial = materials.find((m) => String(m.id) === selectedId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const result = await assignHomework({
        title: title.trim() || selectedMaterial?.title || "Homework",
        materialId: Number(selectedId),
        dueDate,
      });
      setSuccess(`"${result.title}" assigned.`);
      setTitle("");
      setDueDate("");
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not assign the homework.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <ErrorBanner message={error} />
      {success && (
        <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </p>
      )}
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="assign-material">
          Material
        </label>
        <select
          id="assign-material"
          value={selectedId}
          onChange={(e) => setMaterialId(e.target.value)}
          className={inputClass}
        >
          {materials.map((m) => (
            <option key={m.id} value={m.id}>
              {m.title}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="assign-title">
          Assignment title <span className="font-normal text-zinc-400">(optional)</span>
        </label>
        <input
          id="assign-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={selectedMaterial?.title}
          className={inputClass}
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="assign-due">
          Due date
        </label>
        <input
          id="assign-due"
          type="date"
          required
          min={today}
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className={inputClass}
        />
      </div>
      <button type="submit" disabled={busy || !dueDate} className={buttonClass}>
        {busy ? "Assigning…" : "Assign homework"}
      </button>
    </form>
  );
}

export default function TeacherPage() {
  // A student who opens /teacher gets a 403 and is sent to their own dashboard.
  const { data, error, loading, reload } = useDashboard(fetchTeacherDashboard, "/");

  return (
    <DashboardShell title="Teacher dashboard" user={data?.profile ?? null}>
      <ErrorBanner message={error} />
      {loading && <LoadingState />}

      {data && (
        <>
          <Link href="/teacher/create-test" className={`${buttonClass} inline-block`}>
            Create Test
          </Link>

          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Study materials" value={data.stats.materials} />
            <StatCard label="Assignments" value={data.stats.assignments} />
            <StatCard label="Questions in bank" value={data.stats.questionsInBank} />
            <StatCard label="Student submissions" value={data.stats.submissions} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Panel
              title="Upload study material"
              description="Notes you upload here are what quiz questions will be built from."
            >
              <UploadForm onDone={reload} />
            </Panel>
            <Panel
              title="Assign homework"
              description="Pick one of your materials and set a due date."
            >
              <AssignForm materials={data.materials} onDone={reload} />
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Panel title="Your materials">
              {data.materials.length === 0 ? (
                <EmptyState>No materials yet.</EmptyState>
              ) : (
                <ul className="divide-y divide-zinc-100">
                  {data.materials.map((m) => (
                    <li key={m.id} className="flex items-center justify-between gap-4 py-3">
                      <div>
                        <p className="font-medium">{m.title}</p>
                        <p className="text-xs text-zinc-500">Added {formatDate(m.createdAt)}</p>
                      </div>
                      <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-600">
                        {m.questionCount} {m.questionCount === 1 ? "question" : "questions"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="Your assignments">
              {data.assignments.length === 0 ? (
                <EmptyState>No assignments yet.</EmptyState>
              ) : (
                <ul className="divide-y divide-zinc-100">
                  {data.assignments.map((a) => (
                    <li key={a.id} className="flex items-center justify-between gap-4 py-3">
                      <div>
                        <p className="font-medium">{a.title}</p>
                        <p className="text-xs text-zinc-500">
                          {a.materialTitle} · due {formatDate(a.dueDate)}
                        </p>
                      </div>
                      <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-600">
                        {a.submissions} {a.submissions === 1 ? "submission" : "submissions"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        </>
      )}
    </DashboardShell>
  );
}