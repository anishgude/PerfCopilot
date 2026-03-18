"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { samples } from "@/lib/samples";
import type {
  AnalysisResponse,
  BenchmarkPayload,
  RunDetail,
  RunListItem,
  UploadAnalyzeResponse
} from "@/lib/types";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function formatPayload(payload: BenchmarkPayload): string {
  return JSON.stringify(payload, null, 2);
}

function chartRows(payload: BenchmarkPayload) {
  return payload.n.map((size, index) => ({
    n: size,
    runtimeA: payload.runtime_a[index],
    runtimeB: payload.runtime_b?.[index],
    memoryA: payload.memory_a?.[index],
    memoryB: payload.memory_b?.[index]
  }));
}

function StatCard({
  label,
  value
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="glass-panel rounded-3xl p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function toAnalysisFromRun(run: RunDetail): AnalysisResponse {
  return {
    raw_model_text: run.raw_model_text ?? run.error_message ?? "No model output stored.",
    parsed: run.parsed_output_json ?? null,
    computed: {
      slowdown_at_max_pct: run.slowdown_at_max_pct,
      slowdown_at_mid_pct: run.slowdown_at_mid_pct,
      memory_growth_at_max_pct: run.memory_growth_pct
    },
    fit: run.benchmark_json.fit
  };
}

export function Dashboard() {
  const initial = samples[0].payload;
  const [code, setCode] = useState(initial.code);
  const [benchmarkJson, setBenchmarkJson] = useState(formatPayload(initial));
  const [payload, setPayload] = useState<BenchmarkPayload>(initial);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [runsLoading, setRunsLoading] = useState(true);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<number | null>(null);

  const points = chartRows(payload);

  async function fetchRuns() {
    setRunsLoading(true);
    setRunsError(null);
    try {
      const response = await fetch(`${apiUrl}/runs`);
      if (!response.ok) {
        throw new Error(`Failed to load runs (${response.status})`);
      }
      const body = (await response.json()) as RunListItem[];
      setRuns(body);
    } catch (requestError) {
      setRunsError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to fetch analysis history."
      );
    } finally {
      setRunsLoading(false);
    }
  }

  async function loadRun(runId: number) {
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/runs/${runId}`);
      if (!response.ok) {
        throw new Error(`Failed to load run ${runId}`);
      }
      const run = (await response.json()) as RunDetail;
      setActiveRunId(run.id);
      setPayload(run.benchmark_json);
      setCode(run.code);
      setBenchmarkJson(formatPayload(run.benchmark_json));
      setAnalysis(toAnalysisFromRun(run));
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Unable to load run."
      );
    }
  }

  useEffect(() => {
    void fetchRuns();
  }, []);

  async function handleAnalyze() {
    setError(null);
    setUploadMessage(null);
    setIsLoading(true);
    try {
      const parsed = JSON.parse(benchmarkJson) as BenchmarkPayload;
      parsed.code = code;
      setPayload(parsed);
      setActiveRunId(null);

      const response = await fetch(`${apiUrl}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(parsed)
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? `Backend request failed with ${response.status}`);
      }

      const body = (await response.json()) as AnalysisResponse;
      setAnalysis(body);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to analyze the benchmark."
      );
      setAnalysis(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpload() {
    if (!uploadFile) {
      setUploadMessage("Choose a benchmark .json file first.");
      return;
    }
    setUploadLoading(true);
    setUploadMessage(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      const response = await fetch(`${apiUrl}/upload-benchmark`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? `Upload failed with ${response.status}`);
      }
      const body = (await response.json()) as UploadAnalyzeResponse;
      setUploadMessage(`Uploaded and analyzed successfully (run #${body.run_id}).`);
      await fetchRuns();
      await loadRun(body.run_id);
      setUploadFile(null);
    } catch (requestError) {
      setUploadMessage(
        requestError instanceof Error
          ? requestError.message
          : "Upload failed. Please try again."
      );
    } finally {
      setUploadLoading(false);
    }
  }

  function loadSample(index: number) {
    const selected = samples[index].payload;
    setPayload(selected);
    setCode(selected.code);
    setBenchmarkJson(formatPayload(selected));
    setActiveRunId(null);
    setAnalysis(null);
    setError(null);
  }

  async function handleDeleteRun(runId: number) {
    try {
      const response = await fetch(`${apiUrl}/runs/${runId}`, {
        method: "DELETE"
      });
      if (!response.ok) {
        throw new Error("Delete failed.");
      }
      if (activeRunId === runId) {
        setActiveRunId(null);
      }
      await fetchRuns();
    } catch (requestError) {
      setRunsError(
        requestError instanceof Error ? requestError.message : "Unable to delete run."
      );
    }
  }

  function exportReport() {
    if (!analysis) {
      return;
    }
    const blob = new Blob([JSON.stringify({ payload, analysis }, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "perf-copilot-report.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-5 py-8 md:px-8">
      <section className="glass-panel rounded-[2rem] border border-white/70 px-6 py-7 md:px-10 md:py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs uppercase tracking-[0.3em] text-accent">Perf Copilot</p>
            <h1 className="section-title mt-3 text-4xl font-semibold leading-tight md:text-6xl">
              Analyze benchmark uploads like an internal performance platform.
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 md:text-base">
              Upload benchmark files for automatic model diagnosis and persistent history,
              or use the existing manual JSON workflow for ad hoc analysis.
            </p>
          </div>
          <button
            className="rounded-full border border-ink bg-ink px-5 py-3 text-sm font-medium text-white transition hover:-translate-y-0.5"
            onClick={exportReport}
            type="button"
          >
            Export report
          </button>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Upload benchmark JSON</h2>
          <p className="mt-2 text-sm text-slate-600">
            Upload a benchmark file to automatically analyze and persist a new run.
          </p>
          <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
            <input
              accept=".json,application/json"
              className="rounded-xl border border-ink/10 bg-white/80 px-3 py-2 text-sm"
              onChange={(event) =>
                setUploadFile(event.target.files && event.target.files[0] ? event.target.files[0] : null)
              }
              type="file"
            />
            <button
              className="rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={uploadLoading}
              onClick={handleUpload}
              type="button"
            >
              {uploadLoading ? "Uploading..." : "Upload + Analyze"}
            </button>
          </div>
          {uploadMessage ? (
            <p className="mt-3 rounded-xl bg-white/70 px-3 py-2 text-sm text-slate-700">
              {uploadMessage}
            </p>
          ) : null}
        </div>

        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Recent analyses</h2>
          {runsLoading ? (
            <p className="mt-4 text-sm text-slate-600">Loading analysis history...</p>
          ) : null}
          {runsError ? <p className="mt-4 text-sm text-ember">{runsError}</p> : null}
          {!runsLoading && !runsError && runs.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">
              No stored runs yet. Upload a benchmark JSON file to create your first run.
            </p>
          ) : null}
          <div className="mt-4 grid max-h-72 gap-3 overflow-y-auto pr-1">
            {runs.map((run) => (
              <div
                className={`rounded-2xl border bg-white/80 p-4 ${run.id === activeRunId ? "border-accent" : "border-ink/10"}`}
                key={run.id}
              >
                <div className="flex items-start justify-between gap-3">
                  <button
                    className="text-left"
                    onClick={() => void loadRun(run.id)}
                    type="button"
                  >
                    <p className="text-sm font-semibold text-ink">
                      {run.title ?? `${run.language} benchmark`}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {new Date(run.created_at).toLocaleString()}
                    </p>
                  </button>
                  <button
                    className="rounded-full border border-ink/10 px-3 py-1 text-xs text-slate-600 transition hover:border-ember hover:text-ember"
                    onClick={() => void handleDeleteRun(run.id)}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
                <p className="mt-2 text-xs text-slate-600">
                  Status: {run.status} • Slowdown:{" "}
                  {run.slowdown_at_max_pct != null ? `${run.slowdown_at_max_pct}%` : "N/A"}
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  Complexity: {run.a_best_fit ?? "N/A"} → {run.b_best_fit ?? "N/A"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Manual analysis</h2>
          <p className="mt-2 text-sm text-slate-600">
            Existing workflow preserved: edit JSON/code and run ad hoc analysis without
            storing history.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            {samples.map((sample, index) => (
              <button
                className="rounded-full border border-ink/10 bg-white px-4 py-2 text-sm transition hover:border-accent hover:text-accent"
                key={sample.label}
                onClick={() => loadSample(index)}
                type="button"
              >
                {sample.label}
              </button>
            ))}
          </div>
          <div className="mt-6 grid gap-5">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-700">Code snippet</span>
              <textarea
                className="min-h-40 rounded-3xl border border-ink/10 bg-white/70 p-4 text-sm outline-none ring-0"
                onChange={(event) => setCode(event.target.value)}
                value={code}
              />
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-700">Benchmark JSON</span>
              <textarea
                className="min-h-80 rounded-3xl border border-ink/10 bg-white/70 p-4 text-sm outline-none ring-0"
                onChange={(event) => setBenchmarkJson(event.target.value)}
                value={benchmarkJson}
              />
            </label>
          </div>
          <div className="mt-5 flex items-center gap-4">
            <button
              className="rounded-full bg-accent px-5 py-3 text-sm font-medium text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoading}
              onClick={handleAnalyze}
              type="button"
            >
              {isLoading ? "Analyzing..." : "Analyze"}
            </button>
            {error ? <p className="text-sm text-ember">{error}</p> : null}
          </div>
        </div>

        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard
              label="Slowdown at Max n"
              value={
                analysis?.computed.slowdown_at_max_pct != null
                  ? `${analysis.computed.slowdown_at_max_pct}%`
                  : "N/A"
              }
            />
            <StatCard
              label="Slowdown at Mid n"
              value={
                analysis?.computed.slowdown_at_mid_pct != null
                  ? `${analysis.computed.slowdown_at_mid_pct}%`
                  : "N/A"
              }
            />
            <StatCard label="Fit A" value={analysis?.fit.a_best_fit ?? payload.fit.a_best_fit} />
            <StatCard
              label="Fit B"
              value={analysis?.fit.b_best_fit ?? payload.fit.b_best_fit ?? "N/A"}
            />
          </div>
          <div className="glass-panel rounded-[2rem] p-6">
            <h2 className="section-title text-2xl font-semibold">Selected run diagnosis</h2>
            <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
              {activeRunId ? `Active run #${activeRunId}` : "Active run: manual session"}
            </p>
            {analysis?.parsed ? (
              <div className="mt-5 grid gap-4 text-sm text-slate-700">
                <div>
                  <p className="font-semibold text-ink">Summary</p>
                  <p className="mt-1 leading-7">{analysis.parsed.summary ?? "N/A"}</p>
                </div>
                <div>
                  <p className="font-semibold text-ink">Best-fit complexity</p>
                  <p className="mt-1 leading-7">
                    {analysis.parsed.best_fit_complexity ?? "N/A"}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-ink">Regression bullets</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {analysis.parsed.regression_bullets.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-ink">Likely causes</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {analysis.parsed.likely_causes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-ink">Evidence</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {analysis.parsed.evidence.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-ink">Optimization direction</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {analysis.parsed.optimization_direction.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-ink">Risk / edge cases</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {analysis.parsed.risks.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm leading-7 text-slate-600">
                Upload a benchmark or run manual analysis to populate diagnosis details.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Runtime scaling</h2>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points}>
                <CartesianGrid stroke="rgba(13, 27, 30, 0.08)" strokeDasharray="3 3" />
                <XAxis dataKey="n" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  dataKey="runtimeA"
                  name="Runtime A"
                  stroke="#0f766e"
                  strokeWidth={3}
                  type="monotone"
                />
                {payload.runtime_b ? (
                  <Line
                    dataKey="runtimeB"
                    name="Runtime B"
                    stroke="#c2410c"
                    strokeWidth={3}
                    type="monotone"
                  />
                ) : null}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Memory scaling</h2>
          <div className="mt-6 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points}>
                <CartesianGrid stroke="rgba(13, 27, 30, 0.08)" strokeDasharray="3 3" />
                <XAxis dataKey="n" />
                <YAxis />
                <Tooltip />
                <Legend />
                {payload.memory_a ? (
                  <Line
                    dataKey="memoryA"
                    name="Memory A"
                    stroke="#0f766e"
                    strokeWidth={3}
                    type="monotone"
                  />
                ) : null}
                {payload.memory_b ? (
                  <Line
                    dataKey="memoryB"
                    name="Memory B"
                    stroke="#c2410c"
                    strokeWidth={3}
                    type="monotone"
                  />
                ) : null}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Raw model output</h2>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-3xl border border-ink/10 bg-white/70 p-4 text-sm leading-7 text-slate-700">
            {analysis?.raw_model_text ?? "Run an analysis to view the raw model text."}
          </pre>
        </div>
        <div className="glass-panel rounded-[2rem] p-6">
          <h2 className="section-title text-2xl font-semibold">Active benchmark JSON</h2>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-3xl border border-ink/10 bg-white/70 p-4 text-sm leading-7 text-slate-700">
            {formatPayload(payload)}
          </pre>
        </div>
      </section>
    </main>
  );
}
