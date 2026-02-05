# Frontend UI Audit — Extract Current State for Redesign

## Goal

I need you to audit the current frontend UI so I can hand this info to Claude for a design overhaul. The wizards (Scheduler, Report Creation, Property Reports) are the design standard — everything else needs to match their quality level.

**Do NOT change any code.** This is a read-only audit. Just report back what you find.

---

## Part 1: File Structure Map

List every file in `apps/web/src/` that relates to UI layout and pages. I need:

```
apps/web/src/
├── app/                    # List all route folders and their page.tsx files
├── components/             # List all component files, grouped by folder
├── lib/                    # List utility files
└── styles/                 # List any global CSS/Tailwind config
```

Also provide:
- The Tailwind config file contents (`tailwind.config.ts` or similar)
- The global CSS file contents (`globals.css` or similar)
- Any theme/design token files if they exist

---

## Part 2: Layout Components

Find and paste the FULL source code for these layout files:

1. **Root layout** — `app/layout.tsx` (or wherever the shell/sidebar lives)
2. **Sidebar/Navigation component** — The main nav sidebar
3. **Dashboard page** — `app/dashboard/page.tsx` (or the main landing page after login)
4. **Account/Settings page** — `app/settings/page.tsx` or similar
5. **Any shared layout wrapper** — If there's a `DashboardLayout` or `AppShell` component

---

## Part 3: The "Good" Wizards (Design Reference)

Find and paste the FULL source code for these wizard components — these are the design standard we want to match:

1. **Report Creation Wizard** — The multi-step wizard for creating market reports
2. **Property Report Wizard** — The multi-step wizard for creating property/seller reports
3. **Schedule Creation Wizard** — The wizard for setting up scheduled reports

If these are large files, still include them in full. I need to see the exact component patterns, spacing, styling approach, and any shared UI primitives they use.

---

## Part 4: Component Library Inventory

List every shadcn/ui component that's installed (check `components/ui/` folder). For each one, just list the filename:

```
components/ui/
├── button.tsx
├── card.tsx
├── dialog.tsx
├── ...
```

Also check: Are there any custom components (not from shadcn) that are used across multiple pages? List those too with a one-line description of what each does.

---

## Part 5: Current Design Patterns

Answer these specific questions by examining the code:

1. **Color palette** — What are the primary, accent, and background colors used? Check Tailwind config and any CSS variables.

2. **Typography** — What font(s) are loaded? Where are they configured? What size scale is used?

3. **Spacing** — Is spacing consistent? Are they using Tailwind defaults or custom spacing?

4. **Card patterns** — How are dashboard cards styled? (borders, shadows, radius, padding)

5. **Table patterns** — How are data tables styled? (do they use shadcn Table, or custom?)

6. **Form patterns** — How are forms styled outside the wizards vs inside the wizards?

7. **Empty states** — Are there empty state designs, or just blank space?

8. **Loading states** — How are loading states handled? (skeletons, spinners, nothing?)

9. **Page headers** — Is there a consistent page header pattern (title + actions)?

10. **Responsive behavior** — Is the sidebar collapsible? Does the layout adapt to mobile?

---

## Part 6: Screenshots (if possible)

If you have access to a running dev server or can render pages, capture the current state of:

1. Dashboard (main page after login)
2. Sidebar (expanded state)
3. Reports list page
4. Settings/Account page
5. One of the "good" wizards (any step)

---

## Output Format

Please organize your response with clear headers matching the parts above. Paste full file contents in code blocks. For the questions in Part 5, give concise answers with specific code examples.

This entire output will be handed to Claude for analysis, so be thorough and include actual code — not summaries.
