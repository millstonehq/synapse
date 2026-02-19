---
id: SOP-074
type: sop
title: Scale Prometheus Storage SOP
status: approved
owner: SRE Lead
created: '2024-02-04T23:38:10.182Z'
updated: '2025-10-20T09:27:56.136Z'
tags:
  - sop
  - monitoring-stack
summary: Scale Prometheus Storage SOP
related_process: PROCESS-045
related_systems:
  - SYSTEM-038
example: true
---

## Preconditions

- Prometheus storage utilization is above 75% as shown in the Prometheus self-monitoring dashboard, OR storage expansion has been planned as part of a scheduled capacity review
- A change ticket for the storage scaling operation has been approved by the SRE Lead
- The Kubernetes cluster has sufficient node capacity to accommodate the expanded PVC
- You have `kubectl` access to the monitoring namespace with the ability to patch PersistentVolumeClaims

## Materials/Access

- `kubectl` configured for the production cluster with write access to the `monitoring` namespace
- Access to the Prometheus self-monitoring dashboard in Grafana showing TSDB storage metrics
- The change ticket number for this operation
- Terraform or Helm chart repository for the monitoring stack configuration

## Procedure

1. Check current storage utilization: `kubectl exec -n monitoring prometheus-0 -- df -h /prometheus`. Note current usage, available space, and mounted volume size.
2. Check the Prometheus TSDB metrics on the Grafana Prometheus self-monitoring dashboard. Note `prometheus_tsdb_storage_blocks_bytes` and `prometheus_tsdb_head_chunks_storage_size_bytes`.
3. Determine the target storage size. Scale to 150% of current usage, rounded up to the nearest 50 GB, with a minimum of 50 GB headroom.
4. Post in #monitoring-ops: "Starting Prometheus storage scale for [change ticket]. Current: [X GB], Target: [Y GB]. On-call: [your name]."
5. Update the PVC size in the Helm values file or Terraform configuration. Commit and push through the standard GitOps pipeline. Do not patch the PVC directly in production.
6. Once the GitOps sync completes, verify the PVC has been expanded: `kubectl get pvc -n monitoring prometheus-db-prometheus-0`. The `CAPACITY` column should show the new size.
7. Verify Prometheus is still scraping targets correctly: open the Prometheus UI at `/targets` and confirm all targets show `UP` state.
8. Monitor the TSDB storage metrics on the Grafana dashboard for 30 minutes to confirm utilization is within expected range after expansion.
9. Post in #monitoring-ops: "Prometheus storage scale complete. New capacity: [Y GB]. Metrics nominal."

## Validation

- The PVC shows the expanded capacity in `kubectl get pvc`
- Prometheus self-monitoring dashboard shows storage utilization below 60% after expansion
- All Prometheus scrape targets remain in `UP` state with no gaps in the scrape history
- No alerts have fired in the monitoring namespace during or after the operation
- The change ticket is updated with completion timestamp and confirmed capacity

## Rollback

1. If the PVC expansion fails, Prometheus will continue running on the existing storage. Do not restart Prometheus.
2. If Prometheus enters a crash loop after the storage operation, check the pod logs: `kubectl logs -n monitoring prometheus-0`. Common cause is a corrupted TSDB block.
3. If TSDB corruption is suspected, restore from the most recent TSDB snapshot taken before the operation.
4. Escalate to the Platform Lead if storage issues cannot be resolved within 30 minutes, as prolonged storage problems will cause metric data loss.
