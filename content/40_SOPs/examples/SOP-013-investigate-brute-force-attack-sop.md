---
id: SOP-013
type: sop
title: Investigate Brute Force Attack SOP
status: approved
owner: DevOps Lead
created: '2024-09-29T05:40:38.654Z'
updated: '2026-02-16T15:15:19.800Z'
tags:
  - sop
  - user-authentication
summary: Investigate Brute Force Attack SOP
related_process: PROCESS-007
related_systems:
  - SYSTEM-008
example: true
---

## Preconditions

- An alert has fired indicating abnormal failed authentication rate (threshold: > 5 failures per account per 10 minutes or > 1000 global failures per minute)
- The security on-call engineer has acknowledged the alert
- Access to authentication logs and IP reputation lookup tools is available
- An incident ticket has been created

## Materials/Access

- Access to the authentication log aggregation system (Kibana, Splunk, or equivalent)
- Access to the WAF or rate limiting administration console
- Access to the identity management system admin console to review and lock affected accounts
- IP reputation lookup service (e.g., AbuseIPDB, Shodan)
- Incident ticket ID

## Procedure

1. Pull the authentication failure log for the past 60 minutes, filtering for `event_type: login_failed`; group by source IP and target account to identify attack pattern (credential stuffing vs. targeted brute force).
2. Identify the top offending source IP addresses and check each against the IP reputation service to confirm malicious classification.
3. Block the top 10 source IP addresses at the WAF or load balancer level with a 24-hour block and log the block action in the incident ticket.
4. Identify all user accounts that received more than 10 failed login attempts during the attack window; enumerate these as potentially targeted accounts.
5. Force-lock all targeted accounts that received attempts against valid usernames (confirmed by checking whether the account exists in the identity store).
6. Check whether any of the targeted accounts had a successful login during or immediately after the attack window; flag these as potentially compromised and initiate credential reset per SOP-011 procedures.
7. Analyze the attack payload for patterns (common password lists, sequential attempts) to determine if this is an automated credential stuffing campaign.
8. Update the WAF rate limiting rules to reduce the per-IP login attempt threshold based on findings.
9. Notify affected users of the attempted attacks and forced account locks via the standard security notification template.

## Validation

- Authentication failure rate has returned to baseline levels
- All identified offending IP addresses are confirmed blocked at the WAF
- All targeted accounts are confirmed locked or confirmed clean based on access pattern review
- Incident ticket includes a summary of IPs blocked, accounts affected, and any confirmed compromises

## Rollback

1. If legitimate users are being blocked due to shared IP ranges (corporate NAT, VPN), whitelist the specific IP ranges in the WAF after verification with the security team.
2. If account locks affected users who are confirmed clean, unlock accounts and notify users of the temporary lock with an explanation.
3. If the rate limiting threshold changes cause excessive false positives, revert to the previous threshold and schedule a tuning session.
4. Document all rollback actions in the incident ticket and flag them for post-incident review.
