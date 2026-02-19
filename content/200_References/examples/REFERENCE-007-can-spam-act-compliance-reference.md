---
id: REFERENCE-007
type: reference
title: CAN-SPAM Act Compliance Reference
status: draft
owner: Engineering Team
created: '2025-12-20T07:07:09.476Z'
updated: '2025-09-03T02:12:11.106Z'
tags:
  - reference
  - notification-service
summary: CAN-SPAM Act Compliance Reference
upstream_url: https://docs.example.com/can-spam-act-compliance-reference
last_synced: '2026-08-02T12:31:14.952Z'
attribution: Linux Foundation
license: CC BY-SA 4.0
category: api-reference
example: true
---

## Overview

The CAN-SPAM Act (Controlling the Assault of Non-Solicited Pornography And Marketing Act of 2003) is a US federal law that establishes rules for commercial email, gives recipients the right to stop receiving email, and spells out penalties for violations. It applies to any commercial message — defined as email whose primary purpose is advertising or promoting a commercial product or service.

The Notification Service is subject to CAN-SPAM for all marketing and promotional email notifications sent to US-based recipients. Transactional emails (order confirmations, password resets, account alerts) are exempt from most CAN-SPAM requirements but must still honor unsubscribe requests and avoid deceptive headers.

## Key Requirements

The CAN-SPAM Act imposes the following requirements on commercial email senders:

- **Header accuracy**: The `From`, `To`, `Reply-To`, and routing information must accurately identify the sender. Deceptive subject lines that misrepresent the message content are prohibited.
- **Advertisement identification**: Commercial emails must be clearly identified as an advertisement unless the recipient has given affirmative consent (opt-in) to receive messages from the sender.
- **Physical address**: Every commercial email must include a valid physical postal address for the sending organization (street address, PO Box, or registered agent address).
- **Opt-out mechanism**: Every commercial email must include a clear and conspicuous mechanism for recipients to opt out of future messages. The opt-out must work for at least 30 days after the message is sent.
- **Opt-out processing**: Unsubscribe requests must be honored within 10 business days. After an opt-out, the sender may not sell or transfer the recipient's email address (except to a company hired to comply with the opt-out).
- **Third-party accountability**: Hiring a third party (e.g., an email service provider) to send commercial email does not relieve the company of responsibility for CAN-SPAM compliance.

## How the Notification Service Implements These Requirements

The Email Delivery Service and Notification Preference API are the primary systems responsible for CAN-SPAM compliance:

- **Unsubscribe link**: Every email template is required to include a valid unsubscribe link containing a signed `(userId, channel, notificationType)` token. A pre-publish validator blocks any template that is missing this link from being published to the production template registry.
- **One-click List-Unsubscribe**: All commercial emails include the `List-Unsubscribe` and `List-Unsubscribe-Post` headers (RFC 8058), enabling email clients such as Gmail and Outlook to surface a native unsubscribe button. This satisfies the "clear and conspicuous" opt-out requirement.
- **Suppression list**: Addresses that have unsubscribed are added to the Email Delivery Service suppression list. The suppression check runs before every send, preventing delivery to opted-out addresses even if the preference propagation window (30 seconds) has not elapsed.
- **10-day processing guarantee**: The unsubscribe token flow processes opt-out requests synchronously. The preference update is persisted within 500ms of the user clicking "Confirm Unsubscribe." The suppression list entry is effective immediately.
- **Physical address**: Email templates include the company's registered postal address in the footer. Template validators enforce this field's presence.

## Penalties and Risk

Violations of CAN-SPAM can result in civil penalties of up to $51,744 per email (as of 2023 FTC adjustment). Each separate email in a campaign counts as a separate violation. Criminal penalties apply for aggravated violations (harvesting addresses, automated account creation to send spam, etc.).

The primary compliance risk for the Notification Service is failure to honor unsubscribe requests within the required 10-business-day window. The current architecture processes unsubscribes in under 1 second, providing a large compliance margin. The secondary risk is templates that omit the unsubscribe link or physical address — mitigated by the automated pre-publish validator.

## Sync Notes

This reference documents US CAN-SPAM Act requirements as they apply to the Notification Service. For GDPR (EU) and CASL (Canada) requirements, see the Notification Compliance Standard. Re-sync this document when FTC penalty amounts are adjusted or when the FTC issues new guidance on commercial email requirements.
