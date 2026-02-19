---
id: MEETING-049
type: meeting
title: Search UX Improvement Discussion
status: approved
owner: Product Manager
created: '2025-02-05T14:14:30.713Z'
updated: '2025-08-01T12:04:34.969Z'
tags:
  - meeting
  - search-platform
summary: Search UX Improvement Discussion
company: SearchPlatform
topic: Search UX Improvement Discussion
meeting_date: '2025-08-15T21:35:33.693Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Search Platform - UX Improvement Initiative
- **Topic**: Search UX Improvement Discussion
- **Date/Time**: 2025-08-15 02:00 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead (Frontend)
- **Attendees (product)**: Product Manager, UX Researcher, Engineering Manager, QA Lead
- **Context**: User research study completed on search experience; discussing findings and prioritizing UX improvements to reduce abandonment and pogo-sticking rates.

## Observations by Domain

- **Result Snippets**: User research participants reported that snippets "often don't tell me if this is what I'm looking for"; current snippets are keyword-centered and do not provide enough contextual information about the document
- **Zero-Result Experience**: The current zero-result page shows only "No results found" with a search box; users in the study consistently gave up rather than reformulating; a "Did you mean?" suggestion and related content recommendations are expected by users
- **Autocomplete UX**: Autocomplete appears after 300ms delay and disappears on keyboard navigation; users with slower typing speed reported the experience as "flickering"; the 300ms threshold is too short
- **Facet Discoverability**: Filter facets are hidden behind a "Filters" button on mobile; 78% of mobile users in the study did not discover facets existed; facets should be visible inline on mobile
- **Result Type Labeling**: Users could not distinguish between different content types (guide, policy, runbook) in results because the type label is in a small grey font below the title; labeling needs to be more prominent
- **Pagination vs Infinite Scroll**: 65% of study participants preferred infinite scroll over "Next page" pagination for search results; current implementation uses explicit pagination

## Key Metrics & Data Points

- **Pogo-sticking rate**: 18% (benchmark: 12%; study revealed snippet quality as primary cause)
- **Session abandonment after search**: 22% (up from 19% two months ago)
- **Mobile facet discovery rate**: 22% (78% of mobile users unaware facets existed)
- **Zero-result reformulation rate**: 34% (66% of users give up rather than reformulating)
- **Autocomplete adoption on mobile**: 14% (below 30% target)
- **User satisfaction score (SUS)**: 62/100 (target: 75+)

## Preliminary Scorecard Hooks

- Result Snippet Quality: 2/5 - Keyword-centric snippets not providing decision-relevant context; root cause of pogo-sticking
- Zero-Result Experience: 1/5 - No recovery path; most users give up; needs "Did you mean?" and related content
- Mobile Search UX: 2/5 - Facet discoverability critical gap; autocomplete UX issues on mobile
- Result Presentation: 3/5 - Functional but type labels and content hierarchy need refinement
- Performance (perceived): 3/5 - Autocomplete timing needs tuning; no major perceived latency issues for desktop

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Abandonment rate continues rising as mobile share grows | High | High | Product Manager | Prioritize mobile facet redesign and zero-result recovery for Q3 | 2025-09-01 |
| Snippet UX improvements require backend snippet generation changes | Medium | Certain | Principal Engineer | Evaluate passage-level snippet generation as a backend improvement | 2025-09-15 |
| Infinite scroll implementation increases API complexity | Low | Medium | Tech Lead | Use cursor-based pagination API already in place; front-end only change | 2025-09-01 |

## Decisions & Next Steps

### Decisions

- Implement "Did you mean?" suggestions and related content on zero-result pages as top Q3 priority
- Redesign mobile facet presentation to show facets inline (not hidden behind a button)
- Increase autocomplete trigger delay to 500ms and fix keyboard navigation behavior

### Action Items

- Design "Did you mean?" UX flow with spelling correction and query expansion (UX Researcher - 2025-08-29)
- Implement mobile facet redesign (Tech Lead Frontend - 2025-09-12)
- Fix autocomplete trigger delay and keyboard navigation (Tech Lead Frontend - 2025-08-22)
- Explore passage-level snippet generation feasibility (Principal Engineer - 2025-09-15)

### Follow-ups

- A/B test each UX change independently to attribute impact on abandonment and pogo-sticking metrics
- Next UX review meeting in 6 weeks to assess impact of initial changes
