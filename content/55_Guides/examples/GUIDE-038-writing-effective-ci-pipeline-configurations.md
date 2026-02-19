---
id: GUIDE-038
type: guide
title: Writing Effective CI Pipeline Configurations
status: approved
owner: Engineering Team
created: '2024-05-13T11:56:37.825Z'
updated: '2025-04-21T23:15:05.949Z'
tags:
  - guide
  - ci-cd-platform
summary: Writing Effective CI Pipeline Configurations
audience: internal
related_systems:
  - SYSTEM-031
example: true
---

## Why Configuration Quality Matters

A poorly written pipeline configuration is one of the most persistent forms of engineering debt. Slow pipelines increase the feedback loop for developers; flaky configurations erode trust in CI; incorrect caching leads to hours of debugging. This guide shares the patterns that produce fast, reliable, and maintainable CI configurations based on lessons learned across the platform.

## Structuring Jobs for Speed

The primary goal is to get signal to developers as fast as possible. Structure your jobs to fail early and fail cheaply:

- **Run cheap checks first**: Linting and type-checking take seconds and catch most style/syntax issues. Put them in the first job group so developers get feedback without waiting for a full test run.
- **Parallelize independent test suites**: If you have unit tests, integration tests, and end-to-end tests, run them as parallel jobs rather than sequentially. Each can run on its own runner concurrently.
- **Only run expensive stages on necessary branches**: Security scans and image publish steps typically only need to run on the main branch or release tags. Use branch filters to skip them on feature branches where a full publish is not needed.
- **Use matrix builds sparingly**: Testing across multiple runtime versions is valuable, but each matrix entry consumes a runner. Limit matrices to 2-3 versions for routine PRs and expand only for release pipelines.

## Caching Dependencies Correctly

Caching is the single most impactful optimization for most pipelines, but incorrect cache keys cause subtle bugs. The correct approach:

- **Scope your cache key to the dependency manifest**: Use the hash of your lock file as the primary cache key (e.g., `hashFiles('package-lock.json')`). This ensures the cache is invalidated when dependencies change and reused when they haven't.
- **Use a fallback key**: If no exact cache hit exists, fall back to a prefix-only key to restore a partial cache rather than starting completely cold. This cuts install time in half on cache misses.
- **Cache build artifacts separately from dependencies**: If your build produces intermediate artifacts (e.g., compiled TypeScript), cache them with the source file hash as the key.
- **Never cache secrets or environment-specific files**: Ensure your `.dockerignore` and cache path patterns exclude `.env` files, credential stores, and any directory that may contain ephemeral tokens.

## Managing Timeouts and Flaky Jobs

Every job must have an explicit timeout. Without timeouts, a hung job will hold a runner indefinitely and exhaust the pool:

- Set conservative timeouts initially based on observed run times plus a 50% buffer. Review and tighten them quarterly.
- For jobs that are legitimately flaky due to external dependencies (e.g., integration tests hitting a real API), add `retry: 2` to the job definition rather than removing the test. This surfaces the flakiness in the pipeline stats rather than hiding it.
- Mark known-flaky jobs with a comment and link to the tracking ticket. Do not let flaky jobs become invisible infrastructure.

## Common Pitfalls

- **Hardcoding versions**: Use the platform-managed language version variables (e.g., `$NODE_VERSION`) rather than hardcoding `node:18`. This allows the platform team to update runtime versions centrally.
- **Leaking secrets in logs**: Never use `echo` or `print` to output secret values for debugging. Use the CI platform's secret masking feature and debug by logging only the first 4 characters of a credential to confirm it loaded.
- **Skipping the security scan**: It is tempting to comment out the security scan job when it produces noise. Instead, open an exception ticket and configure the scan to suppress known acceptable CVEs by hash rather than disabling the scan entirely.
