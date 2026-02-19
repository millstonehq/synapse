---
id: SOP-068
type: sop
title: Update Base Docker Image SOP
status: approved
owner: DevOps Lead
created: '2024-10-21T23:21:24.869Z'
updated: '2026-11-04T20:54:48.099Z'
tags:
  - sop
  - ci-cd-platform
summary: Update Base Docker Image SOP
related_process: PROCESS-041
related_systems:
  - SYSTEM-033
example: true
---

## Preconditions

- A new version of the base Docker image (e.g., `node:20-alpine`, `golang:1.22`) is available and you have determined an update is required (scheduled update, CVE patch, or end-of-life version)
- You have identified all Dockerfiles in all repositories that reference the base image to be updated
- A security scan of the new base image version has been completed and reviewed

## Materials/Access

- Write access to all repositories containing Dockerfiles that reference the base image
- Access to the container security scanning tool to compare vulnerability counts between old and new base versions
- Access to the CI platform to trigger and monitor pipeline runs for affected services
- The change management system to create and track the update change ticket

## Procedure

1. Run a repository search to identify all `FROM` directives referencing the base image (e.g., `grep -r "FROM node:18" --include=Dockerfile`) and compile the list of affected services.
2. Pull the new base image locally and run the security scanner against it; confirm that the new version has fewer or equal critical/high CVEs compared to the current version; do not proceed if the new version introduces new critical CVEs.
3. For each affected service, open a pull request updating the `FROM` line in the Dockerfile to the new base image version; batch services by team where possible to reduce review burden.
4. Ensure the CI pipeline for each pull request runs a full build and test cycle, including a security scan of the newly built application image.
5. Obtain peer review approval for each Dockerfile change; merge pull requests one service at a time, monitoring the deployment of each before proceeding to the next.
6. After merging, verify the updated image is successfully built, pushed to the registry, and deployed to the staging environment for each service.
7. After all services have been updated and validated in staging, coordinate production promotions according to each service's standard deployment process.
8. Close the change ticket with a summary of all updated services, the new base image version, and the CVE comparison report.

## Validation

- All updated services have passing CI pipelines building from the new base image version
- Security scans of the updated application images confirm reduced or equal CVE counts
- Staging deployments of updated services show no regression in health metrics
- No `FROM` directives remain that reference the old base image version (verified by re-running the search from step 1)

## Rollback

1. If the new base image introduces a build failure, revert the `FROM` directive to the previous version in the affected Dockerfile and re-trigger the pipeline.
2. If the new base image causes runtime failures in staging, revert and open a ticket with the image vendor describing the regression before attempting the update again.
3. If only some services are affected by the regression, roll back only those services while keeping updated services on the new base image.
