# Frontend Architecture

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 15 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4 |
| Component primitives | Radix UI | Latest |
| Component library | shadcn/ui (owned, customized) | Latest |
| Server state | TanStack Query (React Query) | 5 |
| Client state | Zustand | 4 |
| Forms | React Hook Form + Zod | Latest |
| Rich text editor | Tiptap 2 | 2.x |
| Drag and drop | dnd-kit | 6 |
| Charts | Recharts | 2.x |
| Date/time | date-fns | 3 |
| Icons | Lucide React | Latest |
| Testing | Vitest + React Testing Library + Playwright | Latest |

---

## 2. Project Structure

```
apps/web/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group (no main layout)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── accept-invite/
│   │   │   └── page.tsx
│   │   └── layout.tsx            # Auth layout (centered card)
│   │
│   ├── (app)/                    # Main app route group (requires auth)
│   │   ├── layout.tsx            # App shell: sidebar + topbar
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Home dashboard
│   │   ├── pipeline/
│   │   │   ├── page.tsx          # Kanban pipeline view
│   │   │   └── [id]/
│   │   │       ├── page.tsx      # Application workspace
│   │   │       ├── sections/
│   │   │       │   └── [key]/
│   │   │       │       └── page.tsx  # Section editor
│   │   │       └── layout.tsx    # Application workspace layout
│   │   ├── grants/
│   │   │   ├── page.tsx          # Grant database search
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Grant detail page
│   │   ├── funders/
│   │   │   ├── page.tsx          # Funder directory
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Funder profile page
│   │   ├── discovery/
│   │   │   └── page.tsx          # Discovery queue
│   │   ├── calendar/
│   │   │   └── page.tsx          # Deadline calendar
│   │   ├── awards/
│   │   │   ├── page.tsx          # Active awards list
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Award workspace
│   │   ├── analytics/
│   │   │   └── page.tsx          # Analytics dashboard
│   │   ├── documents/
│   │   │   └── page.tsx          # Document vault
│   │   ├── org/
│   │   │   ├── page.tsx          # Org profile overview
│   │   │   ├── profile/
│   │   │   │   └── page.tsx      # Edit profile
│   │   │   ├── financials/
│   │   │   │   └── page.tsx      # Financial data
│   │   │   ├── board/
│   │   │   │   └── page.tsx      # Board members
│   │   │   └── team/
│   │   │       └── page.tsx      # Staff + users
│   │   └── settings/
│   │       └── page.tsx          # Org settings, notifications, billing
│   │
│   ├── api/                      # Next.js API routes (minimal — mostly proxy to FastAPI)
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts      # NextAuth callbacks
│   │
│   ├── layout.tsx                # Root layout
│   └── not-found.tsx
│
├── components/
│   ├── ui/                       # shadcn/ui base components (owned)
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   │
│   ├── app/                      # Application-specific components
│   │   ├── shell/
│   │   │   ├── AppSidebar.tsx
│   │   │   ├── AppTopbar.tsx
│   │   │   └── NotificationBell.tsx
│   │   │
│   │   ├── pipeline/
│   │   │   ├── PipelineKanban.tsx        # Main Kanban board
│   │   │   ├── KanbanColumn.tsx          # Single stage column
│   │   │   ├── ApplicationCard.tsx       # Draggable card
│   │   │   ├── ApplicationListView.tsx   # List mode
│   │   │   ├── StageTransitionDialog.tsx
│   │   │   └── NewApplicationDialog.tsx
│   │   │
│   │   ├── editor/
│   │   │   ├── SectionEditor.tsx         # Tiptap + AI suggestions
│   │   │   ├── AISuggestionPanel.tsx     # Slide-in panel with AI controls
│   │   │   ├── SourceAttributionBar.tsx  # Which atoms were used
│   │   │   ├── CompliancePanel.tsx       # Requirements checklist
│   │   │   ├── WordCountBar.tsx
│   │   │   └── SectionVersionHistory.tsx
│   │   │
│   │   ├── grants/
│   │   │   ├── GrantSearchFilters.tsx
│   │   │   ├── GrantCard.tsx
│   │   │   ├── GrantDetailPanel.tsx
│   │   │   ├── RequiredAttachmentsList.tsx
│   │   │   └── EligibilityBadge.tsx
│   │   │
│   │   ├── discovery/
│   │   │   ├── DiscoveryQueueTable.tsx
│   │   │   ├── RelevanceScoreBadge.tsx
│   │   │   └── DiscoveryReviewDialog.tsx
│   │   │
│   │   ├── calendar/
│   │   │   ├── DeadlineCalendar.tsx      # Month/week/agenda views
│   │   │   └── DeadlineCard.tsx
│   │   │
│   │   ├── analytics/
│   │   │   ├── KPISummaryCards.tsx
│   │   │   ├── WinRateChart.tsx
│   │   │   ├── PipelineValueChart.tsx
│   │   │   ├── FunderConcentrationChart.tsx
│   │   │   └── RevenueForecastChart.tsx
│   │   │
│   │   ├── documents/
│   │   │   ├── DocumentVault.tsx
│   │   │   ├── DocumentUploader.tsx      # Drag-and-drop upload
│   │   │   ├── DocumentPreview.tsx       # PDF/image inline preview
│   │   │   └── DocumentCard.tsx
│   │   │
│   │   ├── awards/
│   │   │   ├── AwardWorkspace.tsx
│   │   │   ├── ExpenditureLog.tsx
│   │   │   ├── ImpactDataForm.tsx
│   │   │   └── StewardshipLog.tsx
│   │   │
│   │   └── org/
│   │       ├── ProfileCompleteness.tsx
│   │       ├── BoardMemberForm.tsx
│   │       └── FinancialsTable.tsx
│   │
│   └── shared/
│       ├── PageHeader.tsx
│       ├── EmptyState.tsx
│       ├── LoadingSkeleton.tsx
│       ├── ConfirmDialog.tsx
│       ├── StatusBadge.tsx
│       ├── UserAvatar.tsx
│       └── CurrencyDisplay.tsx
│
├── hooks/
│   ├── useWebSocket.ts           # WebSocket connection manager
│   ├── useGenerationJob.ts       # Poll/listen for AI job completion
│   ├── useDeadlineAlerts.ts      # Upcoming deadline logic
│   └── useOrgProfile.ts          # Org context hook
│
├── lib/
│   ├── api/                      # API client functions
│   │   ├── client.ts             # Base fetch wrapper (auth headers, error handling)
│   │   ├── applications.ts
│   │   ├── grants.ts
│   │   ├── documents.ts
│   │   ├── analytics.ts
│   │   └── ...
│   │
│   ├── stores/                   # Zustand stores
│   │   ├── ui-store.ts           # Sidebar state, active org, modals
│   │   └── notification-store.ts # In-app notification queue
│   │
│   ├── utils/
│   │   ├── formatters.ts         # Currency, date, word count formatters
│   │   ├── pipeline-stages.ts    # Stage config: labels, colors, transitions
│   │   └── grant-types.ts        # Grant type labels and icons
│   │
│   └── validations/
│       ├── application.ts        # Zod schemas for application forms
│       ├── org-profile.ts
│       └── documents.ts
│
├── types/
│   └── index.ts                  # Re-exports from @orchestragrant/shared
│
├── middleware.ts                 # Route protection (auth check)
└── tailwind.config.ts            # Design tokens
```

---

## 3. State Management Strategy

### 3.1 Server State (TanStack Query)

All data that comes from the API is managed by TanStack Query. This provides:
- Automatic background refresh
- Optimistic updates for pipeline stage changes and task completions
- Shared cache across components (no prop drilling)
- Loading and error states

**Key query keys:**

```typescript
export const queryKeys = {
  org: ['org'],
  orgProfile: ['org', 'profile'],
  orgFinancials: ['org', 'financials'],
  boardMembers: ['org', 'board-members'],
  
  grants: (filters: GrantFilters) => ['grants', filters],
  grant: (id: string) => ['grants', id],
  funders: (filters: FunderFilters) => ['funders', filters],
  funder: (id: string) => ['funders', id],
  
  applications: (filters: ApplicationFilters) => ['applications', filters],
  application: (id: string) => ['applications', id],
  applicationSections: (applicationId: string) => ['applications', applicationId, 'sections'],
  applicationComments: (applicationId: string) => ['applications', applicationId, 'comments'],
  applicationTasks: (applicationId: string) => ['applications', applicationId, 'tasks'],
  
  documents: (filters: DocumentFilters) => ['documents', filters],
  document: (id: string) => ['documents', id],
  
  deadlines: (range: DateRange) => ['deadlines', range],
  
  awards: ['awards'],
  award: (id: string) => ['awards', id],
  
  analytics: {
    dashboard: ['analytics', 'dashboard'],
    winRate: (params: WinRateParams) => ['analytics', 'win-rate', params],
    forecast: ['analytics', 'forecast'],
  },
  
  discoveryQueue: (filters: DiscoveryFilters) => ['discovery', 'queue', filters],
  narrativeAtoms: (filters: AtomFilters) => ['narrative-atoms', filters],
} as const;
```

### 3.2 Client/UI State (Zustand)

Only truly ephemeral UI state lives in Zustand:

```typescript
// lib/stores/ui-store.ts
interface UIStore {
  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  
  // Active context
  activeApplicationId: string | null;
  setActiveApplication: (id: string | null) => void;
  
  // Pipeline view mode
  pipelineView: 'kanban' | 'list';
  setPipelineView: (view: 'kanban' | 'list') => void;
  
  // Active modals
  modals: {
    newApplication: boolean;
    uploadDocument: boolean;
    inviteUser: boolean;
  };
  openModal: (modal: keyof UIStore['modals']) => void;
  closeModal: (modal: keyof UIStore['modals']) => void;
}
```

### 3.3 Real-Time Updates (WebSocket)

The `useWebSocket` hook maintains a single WebSocket connection per authenticated session. Events are dispatched to TanStack Query's cache to trigger re-renders:

```typescript
// hooks/useWebSocket.ts
export function useWebSocket() {
  const queryClient = useQueryClient();
  const { addNotification } = useNotificationStore();
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}?token=${getAccessToken()}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as WSMessage;
      
      switch (message.type) {
        case 'generation.complete':
          // Invalidate section query to trigger refresh
          queryClient.invalidateQueries({
            queryKey: queryKeys.applicationSections(message.payload.application_id)
          });
          break;
          
        case 'application.stage_changed':
          queryClient.invalidateQueries({
            queryKey: queryKeys.applications({})
          });
          break;
          
        case 'discovery.new_grants':
          addNotification({
            title: `${message.payload.count} new grants discovered`,
            link: '/discovery',
            type: 'info'
          });
          queryClient.invalidateQueries({
            queryKey: queryKeys.discoveryQueue({})
          });
          break;
      }
    };
    
    ws.onerror = () => { /* reconnect logic */ };
    
    return () => ws.close();
  }, []);
}
```

---

## 4. Key UI Screens

### 4.1 Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ KPI Cards Row                                              │
│ [Pipeline Value $485K] [Submitted YTD: 18] [Won YTD: 7]   │
│ [Win Rate: 38.9%] [Deadlines Next 30d: 4]                 │
├────────────┬───────────────────────────────────────────────┤
│ Upcoming   │ Recent Activity                               │
│ Deadlines  │                                               │
│ (next 5)   │ - NEA application moved to Board Review       │
│            │ - 12 new grants discovered                    │
│            │ - Knight Foundation guidelines changed        │
│            │ - FY2025 audit indexed (847 atoms)            │
├────────────┴───────────────────────────────────────────────┤
│ Quick Actions                                              │
│ [+ New Application] [Review Discovery Queue (12)]         │
│ [Browse Grant Database]                                    │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Pipeline Kanban

Columns represent pipeline stages. Cards are draggable. Drag triggers a stage confirmation dialog before committing.

Each card shows:
- Grant name + funder logo
- Amount requested
- Deadline (color-coded: red < 7 days, orange < 30 days)
- Assignee avatar
- Checklist progress (e.g., "5/8 tasks complete")

### 4.3 Application Workspace / Section Editor

Three-panel layout:
```
┌──────────────┬─────────────────────────┬──────────────────┐
│ Left Panel   │ Center: Tiptap Editor   │ Right Panel      │
│              │                         │                  │
│ Section nav  │ [Section content...]    │ AI Controls:     │
│ - Org Hist ✓ │                         │ [Generate]       │
│ - Comm Need  │ Word count: 342/400     │ [Regenerate]     │
│ - Proj Desc  │                         │ Emphasis:        │
│ - Eval Plan  │                         │ ○ Community      │
│ - Budget     │                         │ ● Artistic       │
│ - DEI        │                         │ ○ Education      │
│              │                         │                  │
│ Compliance   │                         │ Source atoms:    │
│ 87/100 ✓     │                         │ [2024 NEA app]   │
│              │                         │ [Org profile]    │
│ Attachments  │                         │                  │
│ Checklist    │                         │ Compliance:      │
│ ✓ 990 FY25   │                         │ ✓ Founded year   │
│ ✓ Audit      │                         │ ✓ Growth story   │
│ □ Board List │                         │ ⚠ Milestones     │
└──────────────┴─────────────────────────┴──────────────────┘
```

### 4.4 Grant Database

Filters sidebar on left, results grid/list on right.

Filter controls:
- Grant type (checkboxes)
- Funder type (checkboxes)
- Award range (range slider)
- Geography (dropdown: national / select state)
- LOI required (toggle)
- Match required (toggle)
- Eligibility for org (toggle: show only eligible)
- Last verified within (30/60/90/180 days)

Result card shows:
- Funder logo + name
- Grant name + grant type badge
- Award range ($10K–$100K)
- Next deadline date
- Eligibility badge (Eligible / Review Needed / Ineligible)
- Freshness indicator
- Watchlist star / Start Application button

---

## 5. Design Tokens

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Brand
        brand: {
          50:  '#f0f4ff',
          100: '#e0e9fe',
          500: '#3b5bdb',  // primary
          600: '#3451c7',
          700: '#2c44af',
          900: '#1e2d6e',
        },
        // Pipeline stage colors
        stage: {
          discovered:    '#6b7280',  // gray
          drafting:      '#3b82f6',  // blue
          review:        '#f59e0b',  // amber
          submitted:     '#8b5cf6',  // violet
          awarded:       '#10b981',  // emerald
          declined:      '#ef4444',  // red
        },
        // Urgency / deadline colors
        urgency: {
          critical: '#dc2626',  // < 7 days
          high:     '#f97316',  // < 14 days
          medium:   '#eab308',  // < 30 days
          low:      '#22c55e',  // > 30 days
        },
        // Relevance score colors
        relevance: {
          high:   '#10b981',  // ≥ 0.85
          medium: '#f59e0b',  // 0.70–0.84
          low:    '#f97316',  // < 0.70
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    }
  }
}
```

---

## 6. Performance Considerations

### Route Pre-fetching
- TanStack Query prefetches adjacent pipeline stages on hover
- Grant database results are cached for 5 minutes (user navigates back to same search)

### Code Splitting
- Each route group is a separate bundle via Next.js automatic splitting
- Tiptap editor loads dynamically (heavy library, only needed on section editor pages)
- Recharts loads dynamically (analytics page only)

### Optimistic Updates
- Pipeline stage changes are applied optimistically before API confirmation
- Task completions are applied optimistically
- On error, TanStack Query rolls back and shows error toast

### Image Optimization
- Funder logos served via Next.js `<Image>` with size optimization
- User avatars served via Cloudinary with face detection crop

### Large Form Performance
- Org profile form uses React Hook Form's uncontrolled inputs to prevent re-renders on keystroke
- Financial history table virtualizes rows for orgs with many fiscal years

---

## 7. Accessibility

- All interactive elements have ARIA labels
- Keyboard navigation: Tab order follows visual flow; Escape closes all modals and panels
- Color is never the sole differentiator (stage names + badges + icons used together)
- Screen reader announcements for AI generation completion and WebSocket events
- Focus management: modal close returns focus to trigger element
- WCAG 2.1 AA compliance validated with axe-core in CI

---

## 8. Error Handling

**API errors:**
- 401: Redirect to login, preserve current URL for post-login redirect
- 403: Show "Permission required" in-page state (not redirect)
- 404: Show page-level empty state
- 422: Show field-level validation errors on forms
- 5xx: Show error boundary with retry option; log to Sentry

**AI generation errors:**
- Show error state in the section editor with retry button
- Preserve any existing content (never overwrite with error state)

**WebSocket disconnect:**
- Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Show "Reconnecting..." banner in topbar during disconnect
- On reconnect: invalidate all queries to catch any missed updates

---

*Last Updated: 2026-05-01*
