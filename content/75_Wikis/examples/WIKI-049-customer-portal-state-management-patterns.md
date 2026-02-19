---
id: WIKI-049
type: wiki
title: Customer Portal - State Management Patterns
status: review
owner: Customer Team
created: '2024-07-23T03:35:44.026Z'
updated: '2025-01-13T19:25:54.341Z'
tags:
  - wiki
  - customer-portal
summary: Customer Portal - State Management Patterns
source_repo: https://git.example.com/acme/customer-portal
commit_sha: e4826bf48ed066f7a6fd6f538816fd9167f1637f
generated_at: '2025-08-11T08:28:50.293Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: high
example: true
---

## Overview

The Customer Portal uses Apollo Client for GraphQL state and a minimal set of React patterns for local UI state. There is no global state management library (no Redux, no Zustand). This page documents the approved patterns for managing state in the portal codebase and explains when to use each approach.

The portal's architecture distinguishes between three categories of state:
- **Server state**: Data fetched from the Customer API Gateway (tickets, preferences, activity). Owned by Apollo Client cache.
- **UI state**: Transient client-side state (modal open/closed, form input values, loading indicators). Owned by `useState` or `useReducer` in the relevant component.
- **URL state**: Filter state and pagination cursors that should survive a page refresh or be shareable via URL. Owned by query string parameters via `useSearchParams`.

## Server State: Apollo Client Cache

All data from the Customer API Gateway is managed by Apollo Client. The portal uses a single `ApolloProvider` wrapping the root layout. Server Components use a separate per-request Apollo Client instance (from `@apollo/experimental-nextjs-app-support`).

### Cache normalization

Apollo normalizes cached objects by `__typename` and `id`. All queries must request the `id` field on every object that Apollo needs to normalize (tickets, notifications, activities, customer profile). Without `id`, Apollo cannot deduplicate cached objects and will cause stale data bugs.

```graphql
# Correct: always request id
query TicketList {
  supportTickets {
    id
    subject
    status
    updatedAt
  }
}
```

### Optimistic updates

Use Apollo `optimisticResponse` for mutations where the user expects immediate UI feedback (marking a notification as read, submitting a comment). The optimistic response must exactly match the mutation response shape including `__typename`:

```tsx
mutate({
  variables: { id: notificationId },
  optimisticResponse: {
    markNotificationRead: {
      __typename: 'Notification',
      id: notificationId,
      isRead: true,
    },
  },
})
```

### Cache eviction after mutations

For mutations that add new items to a list (e.g., creating a ticket, submitting a comment), use `cache.modify` in the `update` callback to append the new item to the cached list without a full refetch:

```tsx
update(cache, { data }) {
  cache.modify({
    fields: {
      supportTickets(existingRefs, { toReference }) {
        return [toReference(data.createTicket), ...existingRefs]
      },
    },
  })
}
```

Avoid `refetchQueries` for list mutations in the portal — it triggers a full network round-trip that slows down perceived performance.

## UI State: useState and useReducer

Use `useState` for simple boolean and string state within a single component:

```tsx
const [isOpen, setIsOpen] = useState(false)
const [searchQuery, setSearchQuery] = useState('')
```

Use `useReducer` when a component has multiple related state values that update together (e.g., a multi-step form with validation errors, field values, and submission state):

```tsx
type FormState = { step: number; values: FormValues; errors: FormErrors; isSubmitting: boolean }
const [state, dispatch] = useReducer(formReducer, initialState)
```

Do **not** lift UI state to a React Context unless it needs to be shared across three or more components in different branches of the tree. Over-using Context causes unnecessary re-renders. The only approved Contexts in the portal are `AuthContext` (current customer session) and `RealtimeContext` (WebSocket connection state).

## URL State: useSearchParams

Filter state on list pages (ticket status filter, notification category filter, search query) must be stored in the URL query string so that:
- The user can bookmark or share a filtered view
- Browser back/forward navigation preserves filter state
- The server can render the filtered list on first load

```tsx
// Reading
const searchParams = useSearchParams()
const statusFilter = searchParams.get('status') ?? 'all'

// Writing (use router.push to preserve history)
const router = useRouter()
router.push(`/tickets?status=${newStatus}`)
```

Wrap components that call `useSearchParams()` in a `<Suspense>` boundary in the page component. Next.js requires this for correct static rendering behavior.

## Real-Time State: Apollo Subscriptions

For real-time data (notification count, ticket status updates), use Apollo's `useSubscription` hook in Client Components. The subscription updates the Apollo cache in place, and any `useQuery` result that reads the same cache key will automatically re-render:

```tsx
useSubscription(ON_UNREAD_COUNT_CHANGE, {
  onData: ({ client, data }) => {
    client.cache.writeFragment({
      id: 'ROOT_QUERY',
      fragment: gql`fragment UnreadCount on Query { unreadNotificationCount }`,
      data: { unreadNotificationCount: data.data.unreadCountChanged.unreadCount },
    })
  },
})
```

Do not store subscription results in local `useState`. Write them directly to the Apollo cache so all components that depend on that data update automatically.

## Anti-Patterns to Avoid

- **Prop drilling beyond two levels**: If you are passing a value through three or more component levels, consider co-locating the data fetch in the lowest component that needs it, or extracting a shared Apollo query fragment.
- **Storing server data in useState**: Never copy Apollo query results into local state (`const [tickets, setTickets] = useState(data.tickets)`). Apollo's cache is the source of truth; copying it creates stale data.
- **Using useEffect to sync Apollo cache with local state**: This is the most common cause of stale data bugs in the portal. Access Apollo cache data directly via `useQuery` or `useFragment` instead.
- **Global mutable singletons for UI state**: Do not use a module-level variable or a singleton class to hold UI state that affects rendering. React state must be owned by React components or context.
