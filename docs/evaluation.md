# Evaluation

PerfCopilot emphasizes engineering validation over exaggerated research claims.

## What Is Evaluated Today

- metric computation for slowdown and memory growth
- request validation for benchmark payloads
- structured parsing of model output sections
- persistence and retrieval of analysis runs
- frontend dashboard buildability and lint cleanliness

## What Is Not Claimed

- no formal benchmark-classification leaderboard
- no claim of perfect complexity inference
- no fabricated LLM evaluation metrics

## Practical Quality Signals

- reproducible sample benchmark inputs
- stored example analysis outputs
- backend test suite
- CI for linting, tests, and frontend build

## Future Evaluation Work

- regression test sets for prompt/output stability
- parser robustness measurements across stored runs
- benchmark drift tracking over time
