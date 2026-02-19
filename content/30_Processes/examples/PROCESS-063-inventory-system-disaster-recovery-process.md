---
id: PROCESS-063
type: process
title: Inventory System Disaster Recovery Process
status: review
owner: Engineering Manager
created: '2025-07-02T11:26:26.174Z'
updated: '2026-11-04T23:40:00.586Z'
tags:
  - process
  - inventory-management
summary: Inventory System Disaster Recovery Process
related_standards:
  - STANDARD-017
  - STANDARD-013
related_sops:
  - SOP-028
  - SOP-021
related_systems:
  - SYSTEM-013
example: true
---

## Purpose

Define the process for recovering the inventory management platform ([[SYSTEM-013|Stock Level Calculator]] and its dependent components) from a disaster scenario, ensuring that stock level data integrity is restored, merchants can resume trading, and the event log is consistent before the system is declared fully operational.

## Scope

This process covers recovery from the following disaster scenarios:

- Complete loss of the primary data centre or cloud region where inventory services are hosted
- Irreversible corruption of the stock level PostgreSQL projection database
- ScyllaDB cluster failure causing loss of the hot-path availability data store
- Redis CQRS read model cache invalidation requiring full rebuild from the event log
- Mass data integrity failure affecting more than 5% of active SKUs across multiple merchants

**Out of scope:** Single-service outages recoverable via standard runbooks, individual warehouse sync disruptions, and routine maintenance failovers covered by the high-availability configuration.

## Roles and Responsibilities

- **Incident Commander**: Engineering Manager or on-call senior engineer. Responsible for declaring a disaster, coordinating the recovery team, communicating status to the business, and signing off on data integrity checks before returning the system to merchants.
- **Inventory Platform Lead**: Technical lead for the recovery execution. Responsible for directing recovery steps, making decisions about data restoration vs event log replay, and leading the integrity verification.
- **Database Administrator (DBA)**: Responsible for PostgreSQL and ScyllaDB recovery operations, backup restoration, and confirming data consistency.
- **Infrastructure Lead**: Responsible for cloud infrastructure recovery, networking, Kubernetes cluster restoration, and environment provisioning.
- **Merchant Success Lead**: Responsible for merchant communication, coordinating merchant impact assessment, and managing the merchant-facing status page.

## Triggers

This process is triggered when:

- The inventory platform is unavailable to merchants for more than 30 minutes and standard runbook escalation has not resolved the issue
- The Engineering Manager or an authorised senior engineer formally declares a disaster
- Data integrity checks reveal stock level corruption affecting more than 5% of active SKUs

## Inputs

- Most recent database backup for the PostgreSQL stock level projection database (per [[STANDARD-017|Backup and Recovery Standard]])
- Most recent ScyllaDB backup or snapshot
- Complete Inventory Event Bus event log (event log is the source of truth; all projections are derived from it)
- Recovery environment provisioning runbook ([[SOP-028|DR Environment Provisioning SOP]])
- Integrity verification scripts ([[SOP-021|Data Integrity Verification SOP]])

## Outputs

- Fully operational inventory platform with stock level projections consistent with the event log
- Verified data integrity report confirming stock levels are within tolerance for all active merchants
- Post-disaster incident report detailing timeline, root cause, and corrective actions
- Updated runbooks and process documentation if the disaster exposed gaps

## Steps

1. **Incident Commander declares disaster and assembles recovery team** - The IC notifies the Inventory Platform Lead, DBA, Infrastructure Lead, and Merchant Success Lead. A war room is opened in #inventory-dr-warroom. Merchants are notified of a major incident via the status page.

2. **Infrastructure Lead provisions DR environment** - Following [[SOP-028|DR Environment Provisioning SOP]], the Infrastructure Lead provisions the recovery environment in the secondary region (or restores the primary region). This includes Kubernetes cluster, networking, and all required storage resources. Target: DR environment ready within 60 minutes of declaration.

3. **DBA restores PostgreSQL and ScyllaDB from most recent clean backup** - Using the backup restoration procedures per [[STANDARD-017|Backup and Recovery Standard]], the DBA restores the most recent validated backup to the new environment. Document the backup timestamp — this is the "last known good" point.

4. **Inventory Platform Lead determines replay scope** - Compare the backup timestamp against the current event log head. All events published after the backup timestamp must be replayed to bring projections up to the present state. For large replay windows (> 24 hours), consult [[STANDARD-013|Inventory Data Standard]] for acceptable eventual consistency tolerances during the replay.

5. **Replay events from the Inventory Event Bus** - Using the event replay tooling, consume all events from the backup timestamp to the current log head and re-project stock level changes. Monitor the replay pipeline for errors: events that fail to replay are written to a replay error queue for manual review. Do not proceed until the replay error queue is empty or all errors are adjudicated.

6. **Rebuild Redis CQRS read model** - Once the PostgreSQL projection is current, trigger a full Redis read model rebuild from the PostgreSQL projection. This process typically takes 20-40 minutes for a full merchant catalog. During rebuild, the CQRS read path is unavailable; reservation checks fall through to the PostgreSQL write model (slower but accurate). Notify on-call engineers that reservation latency will be elevated.

7. **Run data integrity verification** - Execute the integrity verification suite per [[SOP-021|Data Integrity Verification SOP]] against a random sample of 5,000 SKUs across at least 10 merchants. Compare system stock levels against any available WMS snapshots or ASN records. All sampled SKUs must be within the configured tolerance (default: ± 2 units or ± 1%). If failures exceed 0.1% of sampled SKUs, do not proceed — escalate to the Incident Commander for a decision on whether to extend verification or accept elevated risk.

8. **Staged merchant re-enablement** - Re-enable inventory services for merchants in staged batches: internal test merchants first, then 5% of production merchants, then 25%, then 100%. Monitor error rates and stock level freshness at each stage. Confirm with the Merchant Success Lead that merchant feedback is normal at each stage before proceeding to the next.

9. **Incident Commander declares recovery complete** - Once all merchants are re-enabled and data integrity verification passes, the IC declares recovery complete on the status page and in #inventory-dr-warroom. Document the recovery timeline, data loss window (gap between last clean backup and recovery point), and any SKUs that could not be recovered.

10. **Post-disaster review** - Within 5 business days, the Inventory Platform Lead leads a post-disaster review. Document the root cause, timeline, gaps in the recovery process, and action items. Update this process and relevant SOPs based on findings.

## Controls

- All disaster recovery exercises must be run at least annually per [[STANDARD-017|Backup and Recovery Standard]]
- Backup restoration from the most recent backup must be verified monthly in a non-production environment
- The data integrity verification step (Step 7) is mandatory; it cannot be skipped even under business pressure to restore service quickly
- Any data loss (stock level records that cannot be recovered from the event log) must be disclosed to affected merchants within 24 hours of recovery
- Post-disaster review findings must be tracked as Jira tickets with owners and resolution deadlines; they are reviewed in the quarterly engineering health review
