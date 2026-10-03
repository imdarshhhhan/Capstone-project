export default function TeacherPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6">
      <section className="w-full max-w-2xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-zinc-900">
          Teacher dashboard
        </h1>
        <p className="mt-2 text-zinc-600">
          You are signed in. Your teaching tools will appear here.
        </p>
      </section>
    </main>
  );
}