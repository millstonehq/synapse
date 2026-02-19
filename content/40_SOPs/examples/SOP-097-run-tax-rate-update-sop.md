---
id: SOP-097
type: sop
title: Run Tax Rate Update SOP
status: approved
owner: SRE Lead
created: '2025-02-13T12:20:04.527Z'
updated: '2025-04-10T11:05:50.856Z'
tags:
  - sop
  - billing-engine
summary: Run Tax Rate Update SOP
related_process: PROCESS-057
related_systems:
  - SYSTEM-046
example: true
---

## Preconditions

- A tax rate change has been identified and documented: jurisdiction code, old rate, new rate, and effective date are confirmed
- Finance Operations has reviewed and approved the tax rate change
- The change is not retroactive to already-finalized invoices (retroactive changes require a separate dispute/credit workflow)
- No monthly billing cycle run is in progress

## Materials/Access

- Write access to the tax rate configuration table in the Billing Engine admin console (role: `billing-tax-operator`)
- The approved tax rate change record from Finance Operations (ticket ID)
- Access to the tax calculation service test tool in the staging environment
- Access to the billing admin console in production

## Procedure

1. Log in to the staging billing admin console and navigate to **Tax Configuration > Rate Table**.
2. Locate the jurisdiction by code and review the current rate. Confirm it matches the old rate in the approved change record.
3. Update the rate to the new value with the effective date set per the approved change. Save the staging change.
4. Run the tax calculation test tool against three representative customer accounts with billing addresses in the affected jurisdiction. Confirm the new rate is applied for invoices dated on or after the effective date, and the old rate is applied for earlier dates.
5. If staging tests pass, repeat steps 2-3 in the production billing admin console.
6. Immediately after updating production, run the tax calculation test tool against one production account in the affected jurisdiction. Confirm the rate is applied correctly.
7. Post in #billing-operations: "Tax rate updated for jurisdiction [CODE]: [OLD_RATE]% → [NEW_RATE]%, effective [DATE]. Change ref: [ID]."
8. Update the Finance Operations approval ticket with the change timestamp and production confirmation.

## Validation

- Tax calculation test tool returns the new rate for invoice dates on or after the effective date
- Tax calculation test tool returns the old rate for invoice dates before the effective date
- No tax-related errors appear in the billing service logs after the update
- Finance Operations confirms the updated rate in the next billing cycle preview

## Rollback

1. If the tax rate was entered incorrectly, navigate to the tax rate record in the billing admin console.
2. Update the rate back to the correct value with an immediate effective date.
3. Run the tax calculation test tool to confirm the corrected rate is now applied.
4. If any invoices were generated with the incorrect rate during the window, initiate the Handle Billing Discrepancy SOP for each affected invoice.
5. Notify Finance Operations of the correction and document the error in the change ticket.
