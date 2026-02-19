---
id: STANDARD-032
type: standard
title: Event Schema Registry Standard
status: approved
owner: Head of Engineering
created: '2024-01-17T17:58:32.294Z'
updated: '2026-01-31T20:48:10.423Z'
tags:
  - standard
  - data-pipeline
summary: Event Schema Registry Standard
related_policies:
  - POLICY-028
  - POLICY-026
example: true
related_systems:
  - SYSTEM-030
  - SYSTEM-026
---

## Area

This standard governs the registration, versioning, and compatibility enforcement of event schemas in the organization's schema registry. It applies to all Avro, Protobuf, and JSON Schema definitions used by Kafka producers and consumers, as well as schemas used in data lake ingestion formats.

## Controls

- All event schemas must be registered in the central schema registry before the producing service is deployed to production
- Schemas must be versioned using semantic versioning; each registered version is immutable
- Breaking changes (field removal, type change, required field addition) are prohibited without a deprecation period of at least 14 days
- Schema compatibility mode must be set to `BACKWARD_COMPATIBLE` or `FULL_COMPATIBLE` for all production topics
- Schema ownership must be declared in the registry metadata; the owning team is responsible for consumer impact assessment
- Unregistered schemas may not be produced to or consumed from production Kafka topics

## Compliance Mappings

- SOC 2: CC8.1 (Change management for data contracts)
- ISO 27001: A.12.1.2 (Change Management)

## Related Policies

- [[POLICY-028|Data Retention and Archival Policy]]
- [[POLICY-026|Data Pipeline Access Control Policy]]
