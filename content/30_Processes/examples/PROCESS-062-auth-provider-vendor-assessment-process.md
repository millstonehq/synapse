---
id: PROCESS-062
type: process
title: Auth Provider Vendor Assessment Process
status: approved
owner: Engineering Manager
created: '2024-09-24T10:31:48.572Z'
updated: '2025-11-07T16:24:14.841Z'
tags:
  - process
  - user-authentication
summary: Auth Provider Vendor Assessment Process
related_standards:
  - STANDARD-011
  - STANDARD-010
related_sops:
  - SOP-013
  - SOP-014
related_systems:
  - SYSTEM-008
example: true
---

## Purpose

This process governs how the platform evaluates and selects third-party authentication and identity providers before integration or adoption. Authentication providers handle sensitive user credentials, session data, and identity assertions — vendors in this space require a more rigorous evaluation than typical SaaS vendors.

The process ensures that any new auth provider meets the platform's security, compliance, and reliability requirements before production use, and that the evaluation is documented for audit purposes.

## Scope

- Identity providers (IdPs) for SSO federation (e.g., Okta, Auth0, Azure AD as a platform IdP)
- MFA delivery providers (e.g., SMS gateways, TOTP library vendors, WebAuthn server implementations)
- Token validation libraries and cryptographic dependencies
- Session management backend alternatives
- Any third-party service that processes user credentials or authentication tokens

## Roles and Responsibilities

- **Engineering Manager**: Sponsors the assessment, approves the final vendor recommendation, and signs off on any deviations from standards
- **Security Engineer**: Leads the security review, performs threat modeling, and reviews the vendor's security documentation and certifications
- **Tech Lead (Auth)**: Evaluates technical fit with the existing [[SYSTEM-008|OAuth Authorization Server]] architecture and integration complexity
- **Compliance Officer**: Reviews vendor compliance certifications against regulatory requirements (SOC 2, ISO 27001, GDPR)
- **Procurement**: Negotiates contract terms, DPA (Data Processing Agreement), and SLA with the selected vendor

## Triggers

- A proposal to adopt a new external authentication or identity service
- An existing auth vendor announces end-of-life, a major security incident, or significant price changes that trigger re-evaluation
- A security review flags an existing vendor as non-compliant with current standards
- Business requirement for a new authentication capability not supportable by existing vendors

## Inputs

- Vendor shortlist (typically 2-4 candidates) from the Tech Lead or Engineering Manager
- Platform authentication requirements document (security, compliance, performance, integration)
- Current architecture context for the [[SYSTEM-008|OAuth Authorization Server]]

## Outputs

- Vendor comparison matrix with scores across evaluation criteria
- Security assessment report per candidate (from Security Engineer)
- Recommended vendor with rationale
- Integration risk assessment and mitigation plan
- Approved procurement engagement (if vendor selected)

## Steps

1. **Define requirements**: Engineering Manager and Tech Lead document the specific capability requirements, security requirements (minimum certifications, data residency), performance requirements (latency SLAs, availability), and integration requirements (APIs, protocols supported). Reference [[STANDARD-010|Token Security Standard]] and [[STANDARD-011|Vendor Security Assessment Standard]] for required security controls.
2. **Compile vendor shortlist**: Tech Lead identifies 2-4 candidate vendors that nominally meet the capability requirements. Sources include market analysis, peer network recommendations, and existing vendor relationships.
3. **Request vendor documentation**: Send each vendor a standard information request: security overview, SOC 2 Type II report or equivalent, penetration test summary (past 12 months), incident history and disclosure policy, SLA terms, and data processing agreement.
4. **Security review**: Security Engineer reviews each vendor's documentation against the platform's requirements. For authentication-critical vendors, conduct a threat modeling session to identify risks specific to the platform's integration pattern. Flag any certification gaps or known security issues.
5. **Technical evaluation**: Tech Lead performs a technical proof-of-concept integration with each shortlisted vendor in the staging environment. Evaluate: API quality and documentation, SDK support, latency profile, error handling, and integration complexity with the existing OAuth Authorization Server.
6. **Compliance review**: Compliance Officer reviews vendor certifications against regulatory requirements. Confirm that a GDPR-compliant Data Processing Agreement is available and that data residency requirements can be met.
7. **Cost and contract analysis**: Procurement obtains pricing from each vendor (per-MAU, per-request, or flat fee models) and reviews SLA terms, including uptime guarantees, incident response commitments, and termination rights.
8. **Scorecard and recommendation**: Engineering Manager compiles a vendor comparison matrix scoring each candidate on security (40%), technical fit (30%), compliance (20%), and cost (10%). Present the recommendation to the engineering and security leadership for approval.

## Controls

- No auth vendor may be used in production without completing this process and receiving written approval from the Engineering Manager
- The vendor assessment documentation must be retained for 3 years for audit purposes
- Security assessments must be refreshed annually for active auth vendors
- Any deviation from the [[STANDARD-011|Vendor Security Assessment Standard]] requirements must be documented with compensating controls
