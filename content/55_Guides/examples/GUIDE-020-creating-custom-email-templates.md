---
id: GUIDE-020
type: guide
title: Creating Custom Email Templates
status: draft
owner: Developer Experience
created: '2024-11-01T00:53:41.668Z'
updated: '2025-03-18T08:35:44.268Z'
tags:
  - guide
  - notification-service
summary: Creating Custom Email Templates
audience: customer
related_systems:
  - SYSTEM-016
  - SYSTEM-018
related_sops:
  - SOP-035
  - SOP-037
example: true
---

## Why This Matters

Email templates that don't work across clients cause broken layouts, missing unsubscribe links, and failed deliveries. Our email template system uses a strict HTML subset to ensure consistency across Gmail, Outlook, Apple Mail, and mobile clients. This guide walks through the constraints and workflow for creating a new email template.

## Template Structure Requirements

Email templates must use table-based HTML layout. Modern CSS layout properties (Grid, Flexbox) are not supported in major email clients. Here is the minimum skeleton for a valid template:

```html
<table width="600" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="font-family: Arial, sans-serif; font-size: 16px; color: #333333;">
      {{body_content}}
    </td>
  </tr>
  <tr>
    <td style="font-size: 12px;">
      <a href="{{unsubscribe_url}}">Unsubscribe</a>
    </td>
  </tr>
</table>
```

Key rules:
- All styles must be inline — no `<style>` blocks or external stylesheets
- Images must use absolute HTTPS URLs
- All dynamic variables use double-brace syntax: `{{variable_name}}`
- All user-provided content must be rendered through the template engine's auto-escape mode

## Dynamic Variables and Data Binding

Each template declares its required variables in a `variables.json` manifest alongside the template file. When you publish a notification event, the `payload` field in your event must provide all declared variables. The Notification Service validates this at dispatch time and will reject events with missing variables rather than send a broken email.

Variable names must be snake_case and must not contain PII field names that are prohibited by the Push Notification Data Privacy Policy (full card numbers, passwords, etc.).

## Template Validation Before Submission

Before submitting a template for review, validate it yourself:

1. Render the template locally using the CLI template preview tool: `npx notification-cli template preview --template=my-template.html --vars=sample.json`
2. Check the output in at least Gmail and Outlook using an email testing tool
3. Verify the unsubscribe link renders and resolves to the correct URL in staging
4. Run the linter: `npx notification-cli template lint --template=my-template.html`

## Next Steps

Submit the validated template through the Notification Template Approval Process. Attach the lint output and a screenshot from the email preview tool to accelerate the review. Once approved, the template is assigned an ID and versioned in the registry.
