# Benchmarking

PerfCopilot expects benchmark payloads that compare one or two implementations across increasing input sizes.

## Payload Schema

Core fields:

- `language`
- `task`
- `code`
- `n`
- `runtime_a`
- `runtime_b`
- `memory_a`
- `memory_b`
- `fit`

The `fit` block carries precomputed best-fit labels and confidence values. PerfCopilot does not claim to infer formal algorithmic complexity from scratch; it uses the provided fit metadata together with the measured curves and benchmark deltas to classify regressions.

## Sample Benchmark Inputs

Located in [`benchmark_data/samples`](/c:/Users/ANISH%20PC/Desktop/performance-analyzer/benchmark_data/samples):

- `sample_regression.json`
- `sample_complexity_shift.json`
- `sample_noisy.json`

These examples cover:

- constant-factor slowdown
- likely complexity-class shift
- noisy but near-flat regressions

## Historical Inputs

[`benchmark_data/historical/latest.json`](/c:/Users/ANISH%20PC/Desktop/performance-analyzer/benchmark_data/historical/latest.json) is used by the PR bot workflow as the current benchmark artifact.
