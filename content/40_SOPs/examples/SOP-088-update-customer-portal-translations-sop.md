---
id: SOP-088
type: sop
title: Update Customer Portal Translations SOP
status: approved
owner: SRE Lead
created: '2025-08-18T01:46:19.919Z'
updated: '2026-11-27T12:39:40.327Z'
tags:
  - sop
  - customer-portal
summary: Update Customer Portal Translations SOP
related_process: PROCESS-049
related_systems:
  - SYSTEM-044
example: true
---

## Preconditions

- Translated strings have been reviewed and approved by a native speaker or professional translator
- All translation files have been updated in the localization repository branch
- CI passes on the branch (no missing key warnings, no format validation errors)
- The translation update is tracked in an approved change ticket

## Materials/Access

- Access to the portal frontend repository with write permissions
- Access to the localization management platform (Phrase or equivalent)
- Translation file export from the localization platform
- Change ticket ID for this translation update

## Procedure

1. Export the approved translation files from the localization platform in the JSON locale format used by the portal.
2. Replace the existing locale files in `src/locales/[locale-code]/` with the exported files; do not manually edit the exported files.
3. Run the locale validation script (`npm run validate:i18n`) to check for missing keys, extra keys, and format string mismatches against the base locale (en-US).
4. If validation reports missing keys, add the missing keys with placeholder text and create a follow-up ticket for the translation team to complete them.
5. Open a pull request targeting the `main` branch; the PR description must include the change ticket ID and a summary of which locales were updated.
6. Ensure at least one reviewer who speaks the updated locale(s) reviews the PR; add the localization team to the review request.
7. Once approved, merge the PR and verify CI passes with no locale validation warnings.
8. After the next portal deployment includes this change, spot-check the updated strings in the staging environment by switching the portal locale.
9. Update the change ticket with the merge commit SHA and confirm the strings are correct in staging.

## Validation

- Portal locale switcher displays updated strings in all modified locales
- No missing key fallbacks to en-US are visible in the updated locale (check browser console for i18n warnings)
- RTL locales (if updated) render text direction correctly in the portal layout
- Locale validation script reports zero errors and zero warnings

## Rollback

1. If incorrect translations are discovered in production, immediately revert the locale files by reverting the merge commit via the portal release process.
2. Re-deploy to production with the previous locale files to restore correct strings.
3. Notify the localization team of the issue with the specific keys that need correction.
4. Once corrected translations are reviewed and approved, re-apply this SOP from step 1.
