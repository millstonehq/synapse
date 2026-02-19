---
id: MEETING-066
type: meeting
title: Container Security Hardening Workshop
status: approved
owner: Product Manager
created: '2025-11-21T13:37:29.543Z'
updated: '2026-10-25T00:38:36.764Z'
tags:
  - meeting
  - ci-cd-platform
summary: Container Security Hardening Workshop
company: CI/CDPlatform
topic: Container Security Hardening Workshop
meeting_date: '2026-05-18T04:28:21.242Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Container Security Program
- **Topic**: Working session to assess current container image security posture and produce a hardening roadmap
- **Date/Time**: 2026-05-18 04:28 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: External penetration test identified three containers running as root and one image with a CRITICAL CVE in production; security team has requested a formal hardening workshop before the next audit

## Observations by Domain

- **Image Base Standards**: No enforced standard for base images; production images range from Alpine to full Ubuntu, making vulnerability management inconsistent and difficult to track
- **Root Container Execution**: 11 of 23 production containers are running as the root user; this violates the organization's security policy and is a finding in the pentest report
- **Privileged Access**: 3 containers are configured with `privileged: true` or `allowPrivilegeEscalation: true` without documented necessity; these represent high blast radius risk
- **Image Signing**: Artifact signing is not yet enforced in the deployment pipeline; images can be substituted in the registry without detection
- **Secrets at Rest**: Two services were found to have secrets baked into their image layers during the pentest; this indicates secrets injection at build time rather than runtime

## Key Metrics & Data Points

- **Containers running as root**: 11 out of 23 production containers (48%)
- **CRITICAL CVEs in production images**: 3 active (down from 7 after emergency patching)
- **Images without signatures**: 23 out of 23 (0% signing adoption)
- **Privileged containers**: 3 (target: 0 without documented exception)
- **Images with secrets baked in**: 2 (both patched post-pentest; root cause was a leaked `.env` in Docker context)

## Preliminary Scorecard Hooks

- Non-Root Execution: 1/5 - Over half of containers running as root; clear policy violation
- Image Provenance: 1/5 - Zero image signing; supply chain integrity not verifiable
- Privilege Escalation Controls: 2/5 - Some PodSecurity policies in place but not fully enforced
- CVE Remediation Speed: 3/5 - Emergency patching effective; systematic prevention still lacking
- Secrets Hygiene: 2/5 - Two incidents of baked-in secrets; runtime injection not universally adopted

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Container escape via root execution enables cluster-wide compromise | Critical | Medium | Principal Engineer | Enforce non-root user in all Dockerfiles; block root containers via admission policy | 2026-06-30 |
| Unsigned image deployment enables supply chain attack | High | Medium | Tech Lead | Implement Cosign image signing in CI pipeline and enforce signature verification at deploy | 2026-07-15 |
| Secrets baked into images are exposed if registry is compromised | High | Low | QA Lead | Audit all Dockerfiles for ADD/COPY of secret files; enforce in pipeline linting | 2026-06-01 |
| Privileged containers escalate impact of application vulnerability | High | Low | Principal Engineer | Document necessity for all 3 privileged containers; eliminate or compensate with seccomp | 2026-06-15 |

## Decisions & Next Steps

### Decisions
- Mandate non-root user definition in all new Dockerfiles immediately; existing root containers must be remediated within 60 days
- Begin phased rollout of Cosign image signing in CI pipeline; all new images signed within 30 days, all existing images signed within 90 days
- Enforce `disallow-privilege-escalation` via Kyverno admission policy in all namespaces by end of June

### Action Items
- Principal Engineer to write the non-root Dockerfile pattern guide and create a remediation tracking spreadsheet for 11 affected services
- Tech Lead to implement Cosign integration in the CI pipeline template and test with 2 pilot services
- QA Lead to run a Dockerfile audit using Hadolint for all 23 services and report secrets exposure findings

### Follow-ups
- Pentest findings to be formally closed with the security team after each mitigation is verified in production
- Schedule a 30-day follow-up to review hardening progress against the scorecard
