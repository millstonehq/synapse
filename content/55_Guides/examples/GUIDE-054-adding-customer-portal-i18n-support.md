---
id: GUIDE-054
type: guide
title: Adding Customer Portal i18n Support
status: approved
owner: Developer Experience
created: '2024-04-30T08:18:38.861Z'
updated: '2025-10-30T09:31:45.480Z'
tags:
  - guide
  - customer-portal
summary: Adding Customer Portal i18n Support
audience: customer
related_systems:
  - SYSTEM-041
  - SYSTEM-044
related_sops:
  - SOP-088
  - SOP-085
example: true
---

## How the Portal i18n System Works

The Customer Portal uses `next-intl` for internationalization. All user-visible strings are stored in locale JSON files under `src/locales/[locale-code]/[namespace].json`. The portal currently supports `en-US`, `fr-FR`, `de-DE`, `es-ES`, `ja-JP`, and `ar-SA` (RTL). When adding a new feature, you are responsible for externalizing all strings into the locale system — not just the English copy.

## Step-by-Step: Adding Strings for a New Feature

1. Identify the namespace for your feature (e.g., `account-settings`, `billing`, `notifications`). If your feature is new, create a new namespace file in each locale directory.

2. Add your keys to the English source file (`src/locales/en-US/[namespace].json`) with descriptive, non-abbreviated key names:
   ```json
   {
     "title": "Account Settings",
     "profile": {
       "heading": "Profile Information",
       "save_button": "Save Changes",
       "save_success": "Your profile has been updated."
     }
   }
   ```

3. Use the `useTranslations` hook in your component:
   ```typescript
   import { useTranslations } from 'next-intl';

   export function ProfileForm() {
     const t = useTranslations('account-settings.profile');
     return <h2>{t('heading')}</h2>;
   }
   ```

4. Run `npm run i18n:check` to verify no keys are missing from non-English locale files; missing keys generate a warning and fall back to English.

5. Submit the English source file in your feature PR. Create a separate ticket for the translation team to fill in non-English locales before the feature ships to non-English customers.

## Handling Dynamic Content

For strings with variable content, use the ICU message format with named placeholders:

```json
{ "greeting": "Welcome back, {name}!" }
```

```typescript
t('greeting', { name: user.displayName })
```

For plurals:
```json
{ "item_count": "{count, plural, =0 {No items} one {# item} other {# items}}" }
```

## RTL Layout Considerations

Arabic (`ar-SA`) requires right-to-left layout. The portal's CSS uses logical properties (`margin-inline-start` rather than `margin-left`) throughout the component library to handle RTL automatically. When building new layout components:

- Use CSS logical properties exclusively; do not use `left`/`right` in new CSS
- Test your feature in RTL mode by appending `?locale=ar-SA` in development
- Pay special attention to icon and arrow directionality; directional icons must be flipped in RTL

## Adding a New Locale

To add a new locale to the portal, open a PR that:
1. Adds the locale code to `src/i18n/config.ts`
2. Creates locale JSON files for all existing namespaces with machine-translated placeholder values
3. Updates the locale switcher component to include the new option
4. Creates a follow-up ticket for native speaker translation review before the locale is made available in production
