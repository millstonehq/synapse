---
id: GUIDE-040
type: guide
title: Container Image Security Scanning Guide
status: approved
owner: Engineering Team
created: '2024-10-31T00:40:01.666Z'
updated: '2025-06-07T10:02:52.457Z'
tags:
  - guide
  - ci-cd-platform
summary: Container Image Security Scanning Guide
audience: partner
related_systems:
  - SYSTEM-032
example: true
---

## Why Image Scanning is Required

Every container image deployed to production contains an operating system layer, language runtime, and application dependencies — any of which may have known vulnerabilities (CVEs). The CI/CD platform runs Trivy against every built image before it can be published to the registry or deployed. This prevents known-vulnerable images from reaching production and gives teams early warning when a dependency requires patching.

Understanding the scanning output and knowing how to act on it is a required skill for every engineer deploying services on the platform.

## Reading Scan Results

Trivy categorizes vulnerabilities by severity: CRITICAL, HIGH, MEDIUM, LOW, and UNKNOWN. The platform pipeline enforces the following gates:

- **CRITICAL**: Blocks the pipeline. The image may not be published until all critical CVEs are resolved or an exception is approved.
- **HIGH**: Blocks the pipeline. Same resolution requirement as CRITICAL.
- **MEDIUM and below**: Reported but do not block. Teams should address these within 30 days.

The scan output in your pipeline logs looks like this:

```
CRITICAL  CVE-2024-1234  libssl3  3.0.11  3.0.12  Fixed in upstream
HIGH      CVE-2024-5678  nodejs   20.10.0 20.11.0 Update available
```

The columns show: severity, CVE ID, affected package, installed version, fixed version, and notes.

## Resolving CVEs

The most common resolution paths, in order of preference:

1. **Update the base image**: Most CVEs in OS packages are fixed in a newer patch release of the base image (e.g., `node:20.11-alpine` instead of `node:20.10-alpine`). Check the base image release notes and update the `FROM` line.
2. **Update the affected dependency**: If the CVE is in an application dependency (e.g., an npm package), update to the fixed version in `package.json` and run `npm install` to update the lockfile.
3. **Remove unused packages**: If the vulnerable package is not actually required by your application, remove it from the image. Minimal images have a smaller attack surface by default.
4. **Request an exception**: If the CVE has no fix available, the vulnerability is not exploitable in your deployment context, or patching would break compatibility, submit an exception request through the security team. Exceptions are time-limited (maximum 90 days) and require a documented mitigation.

## Keeping Scans Clean Over Time

CVEs are discovered continuously, so an image that passes scanning today may fail next week when a new CVE is published against one of its packages:

- Schedule a weekly dependency update PR using Dependabot or Renovate to keep dependencies current; this prevents CVE accumulation.
- Subscribe to the security team's CVE advisory channel (#security-advisories) for zero-day announcements that may require immediate patching outside the normal update cycle.
- Review the scan summary report emailed monthly to service owners, which shows trending CVE counts and calls out images that are falling behind.
