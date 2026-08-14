export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-slate-950 text-slate-100">
      <div className="z-10 max-w-5xl w-full items-center justify-between text-center">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500 bg-clip-text text-transparent mb-4">
          AI Business Intelligence SaaS Platform
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
          Enterprise AI Data Analyst with deterministic numerical accuracy, automated dataset profiling, interactive dashboards, pgvector RAG, and an 11-stage AI query safety pipeline.
        </p>
        <div className="flex justify-center gap-4">
          <a
            href="http://localhost:8000/api/v1/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-medium text-white transition-all shadow-lg shadow-indigo-500/20"
          >
            Explore API Docs
          </a>
        </div>
      </div>
    </main>
  );
}
