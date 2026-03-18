import type { BenchmarkPayload } from "./types";

export const samples: { label: string; payload: BenchmarkPayload }[] = [
  {
    label: "Regression",
    payload: {
      language: "Python",
      task: "Compare two JSON serialization implementations after a refactor.",
      code: "def serialize(rows):\n    out = []\n    for row in rows:\n        out.append({k: str(v) for k, v in row.items()})\n    return out",
      n: [1000, 5000, 10000, 20000],
      runtime_a: [8.2, 39.7, 80.4, 163.2],
      runtime_b: [9.1, 49.4, 105.7, 226.3],
      memory_a: [14.1, 17.2, 21.6, 29.4],
      memory_b: [15.0, 20.8, 28.3, 42.5],
      fit: {
        a_best_fit: "O(n)",
        a_confidence: 0.94,
        b_best_fit: "O(n)",
        b_confidence: 0.9
      }
    }
  },
  {
    label: "Complexity Shift",
    payload: {
      language: "Python",
      task: "Detect whether a new nested lookup accidentally changed scaling.",
      code: "def pair_matches(xs, ys):\n    out = []\n    for x in xs:\n        if x in ys:\n            out.append(x)\n    return out",
      n: [1000, 2000, 4000, 8000],
      runtime_a: [4.8, 9.2, 18.4, 36.7],
      runtime_b: [6.7, 18.3, 57.8, 210.5],
      memory_a: [6.0, 6.1, 6.3, 6.5],
      memory_b: [6.4, 7.0, 8.1, 10.9],
      fit: {
        a_best_fit: "O(n)",
        a_confidence: 0.91,
        b_best_fit: "O(n^2)",
        b_confidence: 0.87
      }
    }
  },
  {
    label: "Noisy",
    payload: {
      language: "Python",
      task: "Inspect a small benchmark with variance but no clear regression.",
      code: "def transform(xs):\n    return [x * 2 for x in xs]",
      n: [500, 1000, 2000, 4000],
      runtime_a: [1.9, 3.8, 7.4, 15.1],
      runtime_b: [2.0, 4.1, 7.5, 15.5],
      memory_a: [2.4, 2.6, 2.8, 3.2],
      memory_b: [2.4, 2.7, 2.9, 3.3],
      fit: {
        a_best_fit: "O(n)",
        a_confidence: 0.88,
        b_best_fit: "O(n)",
        b_confidence: 0.84
      }
    }
  }
];
