---
name: performance-benchmark
description: "Establish performance baselines and catch regressions (load time, Web Vitals, size)."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [performance, benchmark, web-vitals, regression, profiling]
    related_skills: [qa-testing, page-agent]
---

# Performance Benchmark

Use to measure performance and detect regressions before/after a change.

## Procedure
1. **Pick metrics that matter.** Web: page load, Core Web Vitals (LCP/CLS/INP), bundle/asset size,
   request count. API/CLI: latency (p50/p95), throughput, memory, cold start.
2. **Baseline first.** Measure the current/main version under a fixed scenario. Record the numbers
   *and* conditions (machine, network, data size) so comparisons are fair.
3. **Measure the change.** Same scenario, new version. Run several times; report the **median**,
   not a single sample.
4. **Compare & attribute.** Flag regressions beyond noise (e.g. >5–10%) and name the likely cause
   (new dependency, N+1 query, unoptimized asset, blocking call).
5. **Report.** A before/after table with deltas and a verdict: acceptable / regression to fix.

## Rules
- Reproducible scenario or the numbers are meaningless. Warm up; discard the first run.
- Profile before optimizing — don't guess the hot path.

## Done when
You have before/after numbers under a fixed scenario and a clear regression verdict.
