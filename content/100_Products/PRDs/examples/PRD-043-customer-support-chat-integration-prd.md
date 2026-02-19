---
id: PRD-043
type: prd
title: Customer Support Chat Integration PRD
status: accepted
owner: Head of Product
created: '2024-03-19T16:33:55.933Z'
updated: '2026-02-01T04:53:00.920Z'
tags:
  - prd
  - customer-portal
summary: Customer Support Chat Integration PRD
related_tdds:
  - TDD-042
  - TDD-044
example: true
related_standards:
  - STANDARD-053
---

## Summary

Integrate a real-time support chat widget into the Customer Portal, enabling customers to initiate live chat with support agents directly from any portal page without leaving the session. The chat integration replaces the current email-only support initiation flow, which has a median first-response time of 4 hours. Technical design for the notification and real-time infrastructure is in [[TDD-042|TDD-042]] (notification center) and [[TDD-044|TDD-044]] (search integration supporting contextual chat suggestions).

## Goals

- Reduce median first-response time from 4 hours to under 5 minutes for customers who initiate chat during support agent operating hours (9am–6pm)
- Increase support satisfaction rating from 3.6 to 4.2 by enabling faster, contextual resolutions
- Deflect 15% of new support tickets through automated chat suggestions (surfacing relevant help articles before connecting to an agent)
- Enable support agents to handle 3 concurrent chat sessions (vs. 1 phone call), improving agent efficiency

## In Scope

- Chat widget launcher button accessible from every portal page
- Real-time chat session between customer and support agent
- Automated pre-chat flow: bot suggests up to 3 relevant help articles based on the customer's query before connecting to an agent
- Chat history: past sessions visible in the portal for 30 days
- Offline mode: when no agents are available, the widget allows customers to leave a message that creates a support ticket
- Agent availability indicator (online / offline)

## Out of Scope

- AI-powered automated chat bot that handles tickets without agent involvement (future phase)
- Chat on the public marketing site (portal-only)
- Video or voice chat
- Multi-language agent support (English only in v1)

## Users and Flows

**Authenticated customers**: Open the chat widget from any portal page. Enter a question, see up to 3 suggested help articles. If suggestions don't help, connect to an available agent for a live session.

**Support agents**: Use the existing agent console (Zendesk) to receive and respond to chat sessions; the portal widget integrates with Zendesk Chat (Sunshine Conversations API) on the backend.

## Requirements

- Chat widget must be accessible from every portal page via a floating action button
- Widget must pre-populate the customer's account information and most recent open ticket (if any) in the agent console context
- Pre-chat bot must suggest up to 3 help articles based on keyword matching against the customer's typed query before initiating an agent session
- Customer must be able to rate the chat session (thumbs up / thumbs down) after the session closes
- Chat history must be accessible from the portal for 30 days after session close
- When no agents are available, the offline flow must allow the customer to leave a message; the message must create a new support ticket with the chat transcript attached
- Widget must meet WCAG 2.2 Level AA accessibility requirements
- Widget must not degrade portal performance: script load must be deferred; LCP impact < 100ms

## KPIs

- **Median first-response time**: < 5 minutes during agent operating hours within 60 days of launch
- **Pre-chat deflection rate**: >= 15% of chat sessions closed without connecting to an agent (customer resolved via suggested article)
- **Chat CSAT**: >= 4.2 / 5.0 session rating from customers who complete a rating
- **LCP impact**: < 100ms increase in dashboard LCP after widget script load

## Information Architecture

Chat integration documentation:

- TDD in `90_Architecture/TDDs/TDD-042` for notification center and real-time delivery (WebSocket infrastructure shared with chat)
- This PRD in `100_Products/PRDs/PRD-043` for product requirements
- A dedicated runbook in `50_Runbooks/` for chat service outage response

## Data Model

- **ChatSession**: `{ id, customerId, status: (active|closed|offline_message), startedAt, closedAt, agentId, transcript: [ChatMessage] }`
- **ChatMessage**: `{ id, sessionId, senderType: (customer|agent|bot), body, timestamp }`
- **OfflineMessage**: `{ id, customerId, body, ticketId, createdAt }` — converts to SupportTicket on submission

Relationships:
- Customer has many ChatSessions (1:N)
- ChatSession has many ChatMessages (1:N)
- OfflineMessage creates one SupportTicket (1:1)

## Non-Functional

- Chat widget script must load asynchronously and must not block the portal's main thread
- All chat messages must be end-to-end encrypted in transit (TLS); messages are not encrypted at rest (support staff need to read transcripts)
- Chat sessions expire after 10 minutes of inactivity with a warning at 8 minutes
- Zendesk Chat integration must fail gracefully: if the Zendesk API is unavailable, the widget must fall back to the offline message flow

## Constraints

- Backend must integrate with Zendesk Chat (Sunshine Conversations API); no custom agent console will be built
- Widget UI must use the existing portal design system (Radix UI + Tailwind)
- Budget: 3 engineers for 8 weeks
- Must not store chat transcripts longer than 30 days per data retention policy

## Risks

- **Zendesk API outage** disrupts all chat sessions and offline messages. Mitigation: detect Zendesk API errors and fall back to offline message flow immediately; alert on Zendesk API error rate > 5%.
- **Agent capacity** insufficient to handle increased chat volume at launch. Mitigation: enable chat for 10% of customers in week 1; scale based on agent queue depth.
- **Help article index staleness** causes pre-chat bot to suggest outdated articles. Mitigation: sync help article index from CMS on every publish event (< 30 second lag).

## Milestones

### M1: Widget and offline flow (Week 1-3)

#### Deliverables

- Chat widget launcher integrated into portal shell
- Offline message form with SupportTicket creation
- Zendesk Chat Sunshine Conversations API connection

#### Acceptance Criteria

- Widget loads asynchronously; < 100ms LCP impact
- Offline message submitted creates a Zendesk ticket with transcript
- Widget is keyboard navigable and passes axe-core

### M2: Live chat and pre-chat bot (Week 4-6)

#### Deliverables

- Live agent chat session working end-to-end
- Pre-chat bot flow with help article suggestions
- Customer context (account info, recent ticket) populated in agent console

#### Acceptance Criteria

- Customer and agent can exchange messages in real-time with < 500ms delivery latency
- Pre-chat bot suggests up to 3 help articles before agent connect
- Agent console shows customer account tier and most recent open ticket

### M3: History, ratings, and launch (Week 7-8)

#### Deliverables

- Chat history page in the portal (30-day retention)
- Post-session thumbs up/down rating
- Staged rollout (10% → 25% → 50% → 100%)

#### Acceptance Criteria

- Chat history visible under `/support/chat-history`
- Rating submitted and captured in Zendesk CSAT
- Rollout completes with no P95 LCP regression > 100ms
