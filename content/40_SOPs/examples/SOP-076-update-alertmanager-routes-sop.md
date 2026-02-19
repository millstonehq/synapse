---
id: SOP-076
type: sop
title: Update AlertManager Routes SOP
status: approved
owner: Release Manager
created: '2024-04-27T23:19:26.885Z'
updated: '2026-06-04T07:59:03.262Z'
tags:
  - sop
  - monitoring-stack
summary: Update AlertManager Routes SOP
related_process: PROCESS-068
related_systems:
  - SYSTEM-040
example: true
---

## Preconditions

- You have an approved change ticket for the AlertManager routing change
- You understand the current routing tree in AlertManager and can identify where your change fits
- You have validated the new routing configuration in staging AlertManager
- The on-call engineer is aware of the planned change and is prepared to respond if alerts misbehave during the update

## Materials/Access

- Git access to the monitoring configuration repository containing `alertmanager.yml`
- `amtool` CLI configured for the production AlertManager instance (for config validation)
- Access to the staging AlertManager instance for pre-production testing
- AlertManager web UI access (read-only) to observe routing changes after deployment

## Procedure

1. Check out the monitoring configuration repository and locate the AlertManager configuration file (`alertmanager.yml` or equivalent Helm values file).
2. Make the required routing change in a feature branch. Common changes include: adding a new receiver, updating a match rule to route to a different team, or adjusting grouping wait times.
3. Validate the configuration locally with `amtool check-config alertmanager.yml`. The command must return no errors before proceeding.
4. Apply the change to the staging AlertManager and send a test alert to verify it routes correctly to the intended receiver: `amtool alert add --alertmanager.url=http://staging-alertmanager:9093 alertname="TEST" service="your-service"`.
5. Verify the test alert appears at the correct destination (PagerDuty staging, Slack channel, or email as appropriate) and resolves cleanly.
6. Submit a pull request with the configuration change, referencing the change ticket. Request review from the Platform Engineer.
7. After approval, merge the PR. The GitOps pipeline will deploy the change to production AlertManager within 5 minutes.
8. Verify the production AlertManager reload was successful by checking the AlertManager status page (`/-/healthy`) and confirming the config hash matches the expected version.
9. Send a test alert to production AlertManager (using a benign label set) to confirm the new route fires correctly. Resolve the test alert immediately.

## Validation

- `amtool check-config` returns no errors for the updated configuration
- Test alert in staging routes to the correct receiver and resolves cleanly
- Production AlertManager status page shows a successful config reload with the new hash
- Production test alert routes correctly and resolves
- No unintended changes to existing alert routing are observed

## Rollback

1. If the production AlertManager fails to reload the new config, revert the commit in the monitoring repository. The GitOps pipeline will redeploy the previous configuration.
2. If alerts are misrouting after a successful reload, revert the config commit immediately and notify the on-call engineer.
3. Post in #monitoring-ops with the revert reason and the ticket number tracking the fix.
4. Escalate to the Platform Lead if the revert does not restore correct routing within 15 minutes.
