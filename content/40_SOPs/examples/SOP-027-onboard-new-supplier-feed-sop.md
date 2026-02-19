---
id: SOP-027
type: sop
title: Onboard New Supplier Feed SOP
status: approved
owner: DevOps Lead
created: '2025-02-03T12:32:38.769Z'
updated: '2025-02-26T21:43:31.515Z'
tags:
  - sop
  - inventory-management
summary: Onboard New Supplier Feed SOP
related_process: PROCESS-015
related_systems:
  - SYSTEM-013
example: true
---

## Preconditions

- The supplier integration has been approved by the Supplier Relationship Manager and a supplier ID has been assigned
- The supplier has provided their inventory feed API documentation, authentication credentials, and sample data files
- The feed format has been reviewed and a field mapping to the Inventory API Schema Standard has been drafted by an Integration Engineer
- A staging environment endpoint is available for testing the supplier feed before production enablement
- The Inventory Platform Engineer has provisioned staging credentials for the feed ingestion service

## Materials/Access

- Supplier API documentation and authentication credentials (stored in the secrets manager)
- Approved field mapping document for this supplier
- Access to the Feed Management console in the Inventory Admin Portal
- Access to staging Kafka topics for event validation
- Access to #inventory-integrations Slack channel

## Procedure

1. Log in to the Feed Management console and create a new supplier feed record. Enter the supplier ID, feed type (push/pull), and schedule (for pull feeds). Save the record; the system assigns a `feed_id`.
2. Configure the feed credentials by navigating to the feed's Authentication tab and entering the supplier API key and endpoint URL from the secrets manager. Do not paste credentials directly; use the secrets reference format.
3. Upload the approved field mapping document to the feed record. The system will parse the mapping and display a preview of how supplier fields will be translated to inventory fields. Verify the preview looks correct.
4. Enable the feed in staging mode by toggling "Staging Only" to on. Trigger a test pull (or instruct the supplier to send a test push) to generate sample events.
5. Inspect the sample events in the staging Kafka topic browser. Verify that all required inventory fields are populated and that SKU identifiers match the SKU naming convention.
6. Run the feed validation test suite from the admin portal: it checks schema compliance, duplicate handling, and quantity field types. All tests must pass before proceeding.
7. If tests pass, toggle "Staging Only" to off and set feed status to `active`. Monitor the first production feed run in the Grafana feed ingestion dashboard.
8. Confirm with the Inventory Platform Engineer that events are arriving and being processed correctly. Post confirmation in #inventory-integrations.

## Validation

- First production feed run completes without errors in the Feed Management console
- Grafana feed ingestion dashboard shows event throughput matching expected feed volume
- 5 randomly selected SKUs from the supplier feed show correct quantities in the inventory API
- No schema validation errors in the feed ingestion logs for the first 24 hours
- Supplier contact confirms their feed is successfully transmitting to the production endpoint

## Rollback

1. If the feed is ingesting incorrect data, immediately disable it by setting feed status to `paused` in the Feed Management console.
2. Identify the first erroneous event by reviewing the feed ingestion log and note the timestamp.
3. Contact the Inventory Platform Engineer to assess whether any incorrect quantities were committed to inventory records and raise an incident ticket if so.
4. Correct the field mapping document or authentication configuration based on the root cause analysis.
5. Re-enable staging mode and repeat the validation steps before re-activating the production feed.
