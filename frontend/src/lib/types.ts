export type FitSummary = {
  a_best_fit: string;
  a_confidence: number;
  b_best_fit?: string | null;
  b_confidence?: number | null;
};

export type BenchmarkPayload = {
  language: string;
  task: string;
  code: string;
  n: number[];
  runtime_a: number[];
  runtime_b?: number[];
  memory_a?: number[];
  memory_b?: number[];
  fit: FitSummary;
};

export type AnalysisResponse = {
  raw_model_text: string;
  parsed?: {
    summary?: string | null;
    best_fit_complexity?: string | null;
    regression_bullets: string[];
    likely_causes: string[];
    evidence: string[];
    optimization_direction: string[];
    risks: string[];
  } | null;
  computed: {
    slowdown_at_mid_pct?: number | null;
    slowdown_at_max_pct?: number | null;
    memory_growth_at_max_pct?: number | null;
    max_n?: number | null;
    mid_n?: number | null;
  };
  fit: FitSummary;
};

export type UploadAnalyzeResponse = {
  run_id: number;
  status: string;
  computed?: AnalysisResponse["computed"] | null;
  parsed?: AnalysisResponse["parsed"] | null;
  raw_model_text?: string | null;
  error_message?: string | null;
};

export type RunListItem = {
  id: number;
  created_at: string;
  title?: string | null;
  language: string;
  status: string;
  slowdown_at_max_pct?: number | null;
  a_best_fit?: string | null;
  b_best_fit?: string | null;
};

export type RunDetail = {
  id: number;
  created_at: string;
  title?: string | null;
  language: string;
  task: string;
  code: string;
  benchmark_json: BenchmarkPayload;
  raw_model_text?: string | null;
  parsed_output_json?: AnalysisResponse["parsed"] | null;
  slowdown_at_max_pct?: number | null;
  slowdown_at_mid_pct?: number | null;
  memory_growth_pct?: number | null;
  a_best_fit?: string | null;
  b_best_fit?: string | null;
  status: string;
  error_message?: string | null;
};
