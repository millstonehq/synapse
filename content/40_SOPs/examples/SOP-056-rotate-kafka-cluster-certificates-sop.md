---
id: SOP-056
type: sop
title: Rotate Kafka Cluster Certificates SOP
status: review
owner: SRE Lead
created: '2024-06-28T21:54:42.882Z'
updated: '2025-05-06T13:49:11.375Z'
tags:
  - sop
  - data-pipeline
summary: Rotate Kafka Cluster Certificates SOP
related_process: PROCESS-032
related_systems:
  - SYSTEM-027
example: true
---

## Preconditions

- Certificate rotation has been planned and scheduled; all producer and consumer teams have been notified at least 48 hours in advance
- New TLS certificates have been generated and signed by the organization's certificate authority
- The new certificates are staged in the secrets management system (Vault) and ready for distribution
- A maintenance window has been approved; off-peak hours are strongly recommended

## Materials/Access

- Access to Vault or the certificate management system with write permissions for the Kafka certificate paths
- SSH or kubectl access to the Kafka broker nodes (requires elevated access approval)
- Access to the Kafka cluster monitoring dashboard in Grafana
- Access to #kafka-maintenance Slack channel

## Procedure

1. Post in #kafka-maintenance: "Starting Kafka certificate rotation. Maintenance window: [start]-[end]. Contact: [name]."
2. Upload the new broker certificates and CA bundle to Vault at the designated Kafka certificate paths.
3. For each broker, one at a time, update the broker's keystore and truststore with the new certificates using the configuration management tool (Ansible or Terraform).
4. Perform a rolling restart of each broker after certificate update; confirm the broker rejoins the cluster as leader/follower before proceeding to the next.
5. Monitor the Grafana cluster health dashboard during each broker restart; confirm under-replicated partition count returns to 0 before advancing.
6. After all brokers are updated, update the client (producer and consumer) truststore configuration to include the new CA certificate.
7. Trigger a rolling restart of each consumer group application to pick up the new truststore.
8. Verify all producers and consumers reconnect successfully using the new certificates.
9. Post in #kafka-maintenance: "Kafka certificate rotation complete. All brokers and clients using new certificates."

## Validation

- All Kafka brokers show as healthy in the cluster metadata (`kafka-topics --describe`)
- No under-replicated partitions are present after rotation
- Producer and consumer connection error rates return to zero in Grafana
- Certificate expiry dates for the new certificates are confirmed correct via `openssl s_client`

## Rollback

1. If a broker fails to start with the new certificate, restore the previous keystore from Vault backup.
2. Restart the affected broker with the previous certificate and confirm it rejoins the cluster.
3. If multiple brokers are affected, pause the rotation and restore all brokers to the previous certificate before investigating.
4. Notify all consumer and producer teams of the rollback and revised rotation schedule.
5. Open a post-rotation incident ticket documenting the failure mode before rescheduling.
