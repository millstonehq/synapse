---
id: ADR-0027
type: adr
title: Use GitHub Actions Over Jenkins
status: deprecated
owner: Staff Engineer
created: '2024-03-23T00:32:19.532Z'
updated: '2026-02-04T14:23:19.939Z'
tags:
  - adr
  - ci-cd-platform
summary: Use GitHub Actions Over Jenkins
example: true
---

## Context

The organization operated a self-hosted Jenkins infrastructure comprising two primary controllers and a pool of 30 ephemeral build agents. Jenkins had been the standard CI system for approximately four years, but operational burden had grown significantly as the engineering team scaled. The platform team was spending an estimated 15% of its time on Jenkins maintenance: plugin upgrades, agent image management, JVM tuning, and incident response for flaky agent provisioning.

Three specific problems prompted this evaluation: Jenkins pipeline configuration was stored in Groovy Jenkinsfiles that were difficult to read and lint; agent provisioning via Kubernetes plugin was unreliable at scale with cold-start times averaging 90 seconds; and the plugin ecosystem, while vast, had created a dependency management problem where upgrading one plugin frequently broke others. A postmortem on a 4-hour CI outage in Q3 traced the root cause to a Jenkins plugin conflict after a routine update.

The team evaluated GitHub Actions, which was already in use for a small number of repositories, as the candidate replacement. The evaluation criteria included: workflow syntax readability, runner provisioning speed, GitHub integration depth, operational overhead, and total cost.

## Decision

Adopt **GitHub Actions** as the standard CI system for all repositories, replacing Jenkins. Jenkins will be decommissioned after all pipelines are migrated.

All workflow definitions will be stored as `.github/workflows/*.yml` files in each repository. Shared logic will be extracted into reusable workflows in a central `platform/ci-workflows` repository and referenced via `uses:` syntax. The platform team will maintain a set of standard job templates covering common patterns: Go/Node/Python builds, Docker image builds, security scanning, and ArgoCD deployment triggers. A pool of self-hosted GitHub Actions runners on Kubernetes will handle internal network access requirements; public-internet-only jobs will use GitHub-hosted runners to reduce cost.

## Consequences

**Positive:**
- Workflow YAML is declarative, version-controlled alongside code, and readable without specialized CI knowledge
- Native GitHub integration means PR status checks, artifact storage, and deployment environments are first-class features
- Self-hosted runner provisioning via Actions Runner Controller (ARC) on Kubernetes provides faster cold starts than the Jenkins Kubernetes plugin
- Eliminates Jenkins controller maintenance: no JVM, no plugin management, no controller HA setup

**Negative:**
- Migration of ~80 existing Jenkinsfiles requires significant one-time engineering effort
- GitHub Actions has usage limits on GitHub-hosted runners; large test suites require self-hosted runners and ongoing Kubernetes capacity management
- Workflow YAML can become complex for sophisticated pipelines; reusable workflows help but add indirection

**Neutral:**
- Cost structure shifts from self-hosted Jenkins (EC2 + EBS + engineer time) to GitHub Actions minutes (hosted) + Kubernetes capacity (self-hosted); net cost is expected to be neutral
- The platform team retains runner fleet management responsibility, though the operational surface is smaller than Jenkins

## Alternatives Considered

**Continue with Jenkins (modernized):**
- Pro: No migration cost; team has deep Jenkins expertise; plugin ecosystem is unmatched
- Con: Does not address the operational overhead of plugin management and JVM maintenance. Jenkinsfiles remain difficult to lint and review. No path to reducing the 15% maintenance tax.
- Rejected because: Modernization (JCasC, Jenkinsfile linting) would reduce but not eliminate the core problems. The team's time investment would be ongoing rather than a one-time migration.

**CircleCI:**
- Pro: Mature hosted CI with strong Docker support, good parallelism primitives, well-documented
- Con: Requires maintaining separate YAML configuration syntax not shared with GitHub PR integrations. Pricing at scale was 20-30% higher than estimated GitHub Actions cost. No native GitHub deployment environment support.
- Rejected because: The additional cost and context-switching between GitHub and CircleCI UIs were not justified when GitHub Actions met all technical requirements.

**Tekton:**
- Pro: Kubernetes-native, highly flexible, no vendor lock-in, CNCF project
- Con: Extremely verbose YAML pipeline definitions with a steep learning curve. Lacks the developer UX that GitHub Actions provides out of the box. Would require building a custom dashboard and notification system.
- Rejected because: Developer experience is a primary criterion; Tekton's operational complexity would shift the maintenance burden from Jenkins to Tekton without improving developer ergonomics.
