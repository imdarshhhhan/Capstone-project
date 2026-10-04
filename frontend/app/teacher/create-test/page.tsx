"use client";

import Link from "next/link";
import { useState } from "react";

import { DashboardShell, ErrorBanner, Panel } from "@/app/components/DashboardShell";
import { createTest, type GeneratedQuestion } from "@/services/api";

const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none focus:border-zinc-500";
const buttonClass =
  "rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50";

export default function CreateTestPage() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questions, setQuestions] = useState<GeneratedQuestion[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setQuestions([]);
    try {
      const result = await createTest(topic.trim());
      setQuestions(result.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate the test.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardShell title="Create Test" user={null}>
      <Link href="/teacher" className="text-sm text-zinc-600 hover:underline">
        ← Back to dashboard
      </Link>

      <Panel title="Topic" description="Enter a topic and the AI will write a multiple-choice test on it.">
        <form onSubmit={handleSubmit} className="space-y-3">
          <ErrorBanner message={error} />
          <input
            aria-label="Topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Operating Systems"
            className={inputClass}
          />
          <button type="submit" disabled={loading || !topic.trim()} className={buttonClass}>
            {loading ? "Generating… this can take a minute" : "Generate Test"}
          </button>
        </form>
      </Panel>

      {questions.length > 0 && (
        <Panel title={`Generated test – ${questions.length} questions`}>
          <ol className="space-y-6">
            {questions.map((q, i) => (
              <li key={i}>
                <p className="font-medium">
                  {i + 1}. {q.question}
                </p>
                <ul className="mt-2 space-y-1.5">
                  {q.options.map((option, j) => {
                    const isAnswer = option === q.answer;
                    return (
                      <li
                        key={j}
                        className={`rounded-lg border px-3 py-2 text-sm ${
                          isAnswer
                            ? "border-green-300 bg-green-50 font-medium text-green-800"
                            : "border-zinc-200"
                        }`}
                      >
                        {String.fromCharCode(65 + j)}. {option}
                        {isAnswer && " ✓ correct answer"}
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ol>
        </Panel>
      )}
    </DashboardShell>
  );
}
