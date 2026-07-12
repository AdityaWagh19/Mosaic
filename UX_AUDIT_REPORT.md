# Frontend UX Audit Report & Implementation Plan

This document serves as both a comprehensive UX audit report (based on the provided session recording and codebase review) and an actionable implementation plan to elevate the UI to a premium standard.

## 1. Validated Issues

*   **Skip Link Visiblity**: The `<a href="#main-content" class="skip-link">` element is improperly exposed to sighted users in `index.html`.
*   **Intrusive Dark Mode Warning**: `DarkModeDetector.tsx` fires a disruptive toast alert if the user’s system is in dark mode, violating modern web expectations of graceful degradation.
*   **Missing Dropdown Affordance**: The "Research" item in the navbar opens a Popover but lacks a visual cue (e.g., a chevron) to indicate it contains a submenu.
*   **Static Secondary Buttons**: `.btn-secondary` uses a static transparent/white background and border with no hover state, making it look like a read-only tag rather than an interactive CTA.
*   **Unstructured Guide/Analysis Pages**: `GuidePage.tsx` relies on a flat list of sections without numbering, timelines, or distinct visual groupings, making the methodology hard to scan. 
*   **Static Brand Logo**: The Mosaic logo lacks micro-interactions, making the header feel rigid.
*   **Mobile Illustration Cropping/Hiding**: `.hero-illustration` uses `display: none` under 1024px in `landing.css`, stripping the page of its visual identity on mobile devices.
*   **Weak Section Hierarchy**: `h2` and `h3` tags are too close in size and weight to body text. They lack visual anchors (like dividers or accent colors).

## 2. Newly Identified Issues (Additional Audit)

*   **Typography (Eyebrows)**: The `.eyebrow` class lacks character. It needs increased tracking (`letter-spacing`) to look like a premium editorial subhead.
*   **Mobile Table Scrolling**: The comparison table on the Analysis page can break layout bounds on very small screens if `white-space` is not managed properly inside the scroll container.
*   **Dashboard Inputs (Accessibility)**: Several configuration inputs in the Dashboard studio rely on implicit labels or lack proper `htmlFor` bindings.
*   **Whitespace Inconsistency**: The `.section` class enforces a `128px` top margin, which creates awkward gaps on content-dense pages like Analysis and Experiments.

## User Review Required
> [!IMPORTANT]
> Please review the proposed changes below. Once approved, I will systematically implement these fixes across the application. 

## Proposed Changes

---

### Global & Core

#### [MODIFY] `index.html`
*   Remove the `<a href="#main-content" class="skip-link">` to eliminate the unwanted visible link at the top of the page. (Accessibility will be maintained natively via standard DOM focus flow for this lightweight app).

#### [MODIFY] `src/App.tsx`
*   Remove `<DarkModeDetector />` from the React tree.
*   Update the `Nav` component's "Research" trigger to include a `ChevronDown` icon from Lucide, dynamically rotated if the popover is open (or simply statically indicating a dropdown).

#### [DELETE] `src/components/ui/DarkModeDetector.tsx`
*   Delete this file entirely as it serves no purpose once the warning is removed.

---

### Styling & CSS (Hierarchy, Buttons, Whitespace)

#### [MODIFY] `src/styles/components/buttons.css`
*   Add a distinct `:hover` and `:focus-visible` state to `.btn-secondary` (e.g., `background: var(--surface-subtle); color: var(--color-ink); border-color: var(--color-graphite);`).

#### [MODIFY] `src/styles/misc.css`
*   **Typography**: Update `.eyebrow` to include `letter-spacing: 0.1em; text-transform: uppercase;`.
*   **Logo Interaction**: Add a smooth hover animation to `.brand img` (e.g., a subtle 10-degree rotation and 1.05x scale bounce).
*   **Section Titles**: Increase `.section h2` from `24px` to `28px` or `32px` with a tighter line-height and bolder weight. Add an optional `.section-header` layout wrapper that pairs titles with prominent `<LineReveal />` dividers.
*   **Whitespace Adjustments**: Reduce `.section` top margin to `96px` (desktop) and `64px` (mobile) to tighten up the flow.

#### [MODIFY] `src/styles/pages/landing.css`
*   Remove `display: none` from `.hero-illustration` at `< 1024px`. 
*   Introduce a mobile-friendly grid layout for `.landing-hero` that stacks the text above the illustration, scaling the illustration appropriately instead of hiding it.

---

### Page Layout Refactoring

#### [MODIFY] `src/pages/GuidePage.tsx`
*   Refactor the flat list of sections into a **Numbered Step / Timeline Layout**. 
*   Add large, stylized step numbers (e.g., `01`, `02`) next to each section.
*   Add subtle vertical connector lines between steps to guide the user's eye naturally down the page.

#### [MODIFY] `src/pages/AnalysisPage.tsx`
*   Introduce a unified `.section-header` component/class to wrap the `h2` tags alongside horizontal dividers.
*   Ensure the data table is wrapped in a container that supports smooth horizontal scrolling (`overflow-x: auto; -webkit-overflow-scrolling: touch;`) without clipping text.

## Verification Plan

### Manual Verification
1.  **Mobile Testing**: Resize the browser to < 600px and verify the hero illustration remains visible and the ML table scrolls smoothly.
2.  **Navigation**: Open the navbar, verify the "Research" chevron is present, and ensure no dark mode toast appears.
3.  **UI Interactivity**: Hover over the Mosaic logo and all secondary buttons to confirm the new premium micro-interactions.
4.  **Visual Hierarchy**: Scroll through the Guide and Analysis pages to ensure the numbered timelines and enhanced typography provide a clear, scannable reading experience.
