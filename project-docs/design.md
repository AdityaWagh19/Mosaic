# Mosaic — Design Specification

**Version:** 1.0  
**Theme:** Light (single theme — no dark mode)  
**Source material:** `DESIGN (2).md`, `theme.css`, `variables.css`, `tokens.json`

This document is the single source of truth for all design decisions in the
Mosaic frontend. It supersedes and consolidates the four source files listed
above. Developers and designers should reference only this document. The source
files are retained for traceability.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Design Principles](#2-design-principles)
3. [Color System](#3-color-system)
4. [Surfaces and Elevation](#4-surfaces-and-elevation)
5. [Typography](#5-typography)
6. [Spacing and Layout](#6-spacing-and-layout)
7. [Border Radius](#7-border-radius)
8. [Shadows](#8-shadows)
9. [Imagery and Illustration](#9-imagery-and-illustration)
10. [Components](#10-components)
11. [Navigation](#11-navigation)
12. [Forms](#12-forms)
13. [Charts and Data Visualization](#13-charts-and-data-visualization)
14. [Interaction States](#14-interaction-states)
15. [Responsive Design](#15-responsive-design)
16. [Accessibility](#16-accessibility)
17. [Design Tokens Reference](#17-design-tokens-reference)
18. [CSS Custom Properties](#18-css-custom-properties)
19. [Frontend Conventions](#19-frontend-conventions)
20. [Do's and Don'ts](#20-dos-and-donts)

---

## 1. Design Philosophy

The visual language of Mosaic is described as a **printed monograph on warm
cream paper** — a confident editorial-monochrome system where restraint is the
identity. The interface is deliberately austere: no chromatic accent colors, no
decorative gradients in UI chrome, no colored badges or interactive state fills.

The eye is drawn to exactly two things: the editorial serif headlines, and the
vivid abstract gradient artwork that serves as the only chromatic content in the
system. Everything else is warm neutral ink on warm neutral paper.

The aesthetic draws from the same lineage as Replicate, Mistral AI, Linear, and
Anysphere — warm grayscale interfaces where confident typographic hierarchy and
deliberate restraint carry more weight than visual decoration.

**Tagline:** *A confident editorial monochrome where the only color is the
artwork and the only ornament is the serif.*

---

## 2. Design Principles

**Monochrome by conviction, not by limitation.**
The system contains zero chromatic tokens for UI elements. Warm neutrals (Ink,
Stone, Paper Warm, Paper Cool, Mist, White) carry the entire interface. Any
impulse to introduce a brand accent color breaks the identity.

**Typography is the interface.**
Two very different typographic voices — a classical bracketed serif (Egyptienne F)
and a geometric humanist sans (Diatype) — create a rhythm that no single
typeface can achieve. The contrast between a 94px serif headline and an 11px
mono label is the system's signature.

**Spaciousness signals quality.**
Generous vertical breathing room, 96px section gaps, and wide whitespace between
elements are not wasted space — they are the design. Crowded layouts break the
editorial feel immediately.

**One shadow, used sparingly.**
A single 12px soft drop shadow at 10% opacity exists in the system. It is applied
exclusively to elevated feature cards. It does not appear on buttons, inputs,
modals, or any other element.

**Gradient artwork is content, not decoration.**
Abstract high-chroma gradient compositions appear only on content cards (use case
cards). They are the brand's sole chromatic expression. They are never used as
background panels, button fills, or section treatments.

---

## 3. Color System

The system uses exactly seven color tokens. There are no semantic color aliases
(success green, error red, warning yellow) — status communication relies on
iconography and text, not color.

### Color Tokens

| Name | Value | CSS Token | Role |
|---|---|---|---|
| Ink | `#272421` | `--color-ink` | Primary text, filled button background, dark inverse surfaces, hairline borders on dark contexts, logo mark. The warmest near-black in the system — never substitute with pure `#000000`. |
| Paper Warm | `#edebe8` | `--color-paper-warm` | Hairline borders, dividers, input outlines, card surface backgrounds, secondary button backgrounds, soft section bands. Do not use as a CTA fill. |
| Paper Cool | `#e3e3e2` | `--color-paper-cool` | Inset wells, table header backgrounds, slightly recessed containers. One step cooler and darker than Paper Warm — used sparingly to create layered depth. |
| Mist | `#eeeeed` | `--color-mist` | Subtle dividers, very low-contrast borders, badge fill backgrounds, hover wash on neutral surfaces. One step lighter than Paper Warm — the finest detail layer. |
| Stone | `#7d7c7a` | `--color-stone` | Muted body copy, secondary metadata, disabled labels, low-emphasis icon strokes, step number labels, logo grayscale rendering. The mid-warm-gray. |
| Charcoal | `#333333` | `--color-charcoal` | In-content link text and link underline/border when a link must feel slightly less assertive than primary Ink text. |
| White | `#ffffff` | `--color-white` | Page canvas, button text on Ink fills, navigation background, card image overlay text. |

### Color Pairing Rules

- **Primary text on White canvas:** Ink (`#272421`) — always
- **Secondary / muted text:** Stone (`#7d7c7a`)
- **Button text on dark fill:** White (`#ffffff`)
- **Hairline borders:** Paper Warm (`#edebe8`)
- **In-content links:** Charcoal (`#333333`)
- **Status indicators:** Stone for neutral state; rely on icons (check, cross, dot) rather than color for success/error states

### What is Not in This System

- No chromatic accent color (blue, green, purple, orange)
- No success green, error red, or warning amber
- No gradient fills on UI chrome
- No color-coded data categories in the simulation UI (use Ink-based monochrome patterns or the single shadow for emphasis)

---

## 4. Surfaces and Elevation

Four surface levels create depth through warm neutrals alone. No chromatic
differentiation between levels.

| Level | Name | Value | CSS Token | Purpose |
|---|---|---|---|---|
| 1 | Canvas | `#ffffff` | `--surface-canvas` | Page background; base layer for all content sections |
| 2 | Soft Surface | `#edebe8` | `--surface-soft-surface` | Card backgrounds, feature panels, secondary button fills, soft section bands |
| 3 | Cool Surface | `#e3e3e2` | `--surface-cool-surface` | Inset wells, table headers, recessed containers |
| 4 | Inverse Surface | `#272421` | `--surface-inverse-surface` | Filled primary buttons, dark badges, rare fully inverted sections |

Elevation is communicated through:
1. Surface color step (Canvas → Soft Surface → Cool Surface)
2. The single shadow token (`--shadow-md`) applied to level-2 elevated cards
3. A 1px border in `--color-paper-warm` where a card edge needs explicit definition

---

## 5. Typography

The system uses three typefaces in tightly constrained roles. Using any typeface
outside its defined role corrupts the typographic identity.

### Typeface Definitions

#### Egyptienne F LT — `--font-egyptienne-f-lt`

Classical bracketed serif. The editorial signature of the system.

- **Primary substitutes:** Source Serif Pro, PT Serif
- **Weights in use:** 400 (primary), 500 (tokens.json confirms both used at display sizes)
- **Allowed sizes:** 22px, 77px, 94px (per design tokens)
- **Line heights:** 0.90 (at 94px), 1.00 (at 77px), 1.20 (at 22px)
- **Letter spacing:** -0.028em to -0.030em (tight at all sizes)
- **OpenType:** `liga` enabled
- **Usage:** Hero headlines, section display headings only. Never body copy, never UI chrome, never below 22px.

**Fallback stack:**
```css
'Egyptienne F LT', ui-sans-serif, system-ui, -apple-system,
BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
```

---

#### Diatype — `--font-diatype`

Geometric humanist sans. The primary workhorse for UI and body.

- **Primary substitute:** Inter
- **Weights in use:** 400 (body, most UI), 500 (emphasized labels, subheadings, card overlay text), 700 (reserved — rare weight contrast only)
- **Allowed sizes:** 14px, 15px, 18px, 24px, 32px, 48px, 72px, 88px
- **Line heights:** 1.20, 1.30, 1.40, 1.43
- **Letter spacing:** -0.030em at 32px and above (tight); +0.018em at 14–24px (open)
- **Usage:** Navigation body links (non-label), body paragraphs, subheadings, sans-serif display text, card overlay labels

**Fallback stack:**
```css
'Diatype', ui-sans-serif, system-ui, -apple-system,
BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
```

---

#### Diatype Mono — `--font-diatype-mono`

Monospaced geometric. The typographic furniture of the system.

- **Primary substitutes:** JetBrains Mono, IBM Plex Mono
- **Weight in use:** 400 only
- **Allowed sizes:** 11px, 13px
- **Line heights:** 1.00, 1.40
- **Letter spacing:** 0.030em (default), 0.090em (uppercase tracked labels)
- **Usage:** Navigation item labels (uppercase), button labels (uppercase), step numbers (UPPERCASE), category tags, badge text, caption labels

**Fallback stack:**
```css
'Diatype Mono', ui-monospace, SFMono-Regular, Menlo, Monaco,
Consolas, monospace
```

---

### Type Scale

The named scale from `variables.css` and `DESIGN (2).md`. All sizes correspond
to CSS custom properties.

| Role | Size | Font | Weight | Line Height | Letter Spacing | CSS Token |
|---|---|---|---|---|---|---|
| caption | 11px | Diatype Mono | 400 | 1.40 | +0.33px | `--text-caption` |
| body | 15px | Diatype | 400 | 1.43 | +0.27px | `--text-body` |
| subheading | 18px | Diatype | 400/700 | 1.30 | +0.32px | `--text-subheading` |
| heading-sm | 24px | Diatype | 500 | 1.30 | +0.43px | `--text-heading-sm` |
| heading | 32px | Diatype | 400 | 1.20 | -0.96px | `--text-heading` |
| heading-lg | 48px | Diatype | 500 | 1.20 | -1.44px | `--text-heading-lg` |
| display | 77px | Egyptienne F LT | 400/500 | 1.00 | -2.16px | `--text-display` |
| display-xl | 94px | Egyptienne F LT | 400/500 | 0.90 | -2.82px | `--text-display-xl` |

**Note on weight conflict:** `DESIGN (2).md` specifies weight 400 for Egyptienne F at display sizes; `tokens.json` specifies weight 500 for the same sizes. Both are acceptable — 400 gives a lighter editorial feel, 500 gives slightly more authority. Use 400 as the default; 500 is permitted for hero hero contexts requiring maximum impact.

### Extended Typography Steps (from tokens.json)

The design tokens include additional granular steps not named in the scale table above. These are implementation-level references:

| Token Key | Font | Size | Weight | Line Height | Usage |
|---|---|---|---|---|---|
| `xs` | Diatype Mono | 11px | 400 | 1.4 | Caption, step labels |
| `sm` | Diatype Mono | 13px | 400 | 1.0 | Compact button labels |
| `sm-2` | Diatype Mono | 13px | 400 | 1.4 | Nav items, standard button labels |
| `sm-3` | Diatype | 14px | 400 | 1.43 | Dense body text |
| `sm-4` | Diatype | 14px | 400 | 1.0 | Compact UI text |
| `base` | Diatype | 15px | 400 | 1.4 | Body copy (default) |
| `lg` | Diatype | 18px | 400 | 1.3 | Subheadings |
| `lg-2` | Diatype | 18px | 400 | 1.0 | Compact subheadings |
| `lg-3` | Diatype | 18px | 400 | 1.4 | Relaxed subheadings |
| `lg-4` | Diatype | 18px | 700 | 1.3 | Bold subheading (rare) |
| `xl` | Egyptienne F LT | 22px | 400 | 1.2 | Small serif heading |
| `2xl` | Diatype | 24px | 500 | 1.3 | Section heading-sm |
| `3xl` | Diatype | 32px | 400 | 1.2 | Sans section heading |
| `5xl` | Diatype | 48px | 500 | 1.0 | Large sans heading |
| `5xl-2` | Diatype | 72px | 500 | 1.0 | Extra large sans display |
| `5xl-3` | Egyptienne F LT | 77px | 500 | 1.0 | Serif display |
| `5xl-4` | Diatype | 88px | 500 | 0.9 | Large sans display |
| `5xl-5` | Egyptienne F LT | 94px | 500 | 0.9 | Hero serif display (largest) |

### Type Pairing Logic

The contrast between Egyptienne F at 77–94px and Diatype Mono at 11–13px is the
system's signature rhythm. Never flatten it by substituting a sans-serif for the
serif, or by removing the mono labels. The three voices occupy distinct
non-overlapping roles: the serif speaks in headlines, Diatype carries functional
content, and Diatype Mono acts as typographic furniture.

---

## 6. Spacing and Layout

### Base Unit

The spacing system uses a **4px base unit**. All spacing values are multiples
of this unit. Density is set to **comfortable** — not compact, not loose.

### Spacing Scale

| Step | Value | CSS Token |
|---|---|---|
| 1 | 4px | `--spacing-4` |
| 2 | 8px | `--spacing-8` |
| 3 | 12px | `--spacing-12` |
| 4 | 16px | `--spacing-16` |
| 5 | 20px | `--spacing-20` |
| 6 | 24px | `--spacing-24` |
| 8 | 32px | `--spacing-32` |
| 12 | 48px | `--spacing-48` |
| 14 | 56px | `--spacing-56` |
| 15 | 60px | `--spacing-60` |
| 16 | 64px | `--spacing-64` |
| 19 | 76px | `--spacing-76` |
| 20 | 80px | `--spacing-80` |
| 21 | 84px | `--spacing-84` |
| 22 | 88px | `--spacing-88` |
| 34 | 136px | `--spacing-136` |
| — | 4px | `--spacing-unit` (base unit reference) |

### Layout System

| Property | Value | CSS Token |
|---|---|---|
| Page max-width | 1200px | `--page-max-width` |
| Horizontal gutter | 24px | (applied via page-max-width container padding) |
| Section gap (vertical rhythm) | 96px | `--section-gap` |
| Card internal padding | 24px | `--card-padding` |
| Element gap (within components) | 8px | `--element-gap` |

### Grid

- **Desktop (>= 1024px):** 3-column for use case cards; 2-column for feature cards
- **Content column:** Centered within 1200px max-width with 24px horizontal padding on each side
- **Card gap:** 12–16px between cards in a grid
- No sidebar layouts. No mega-menus. Single centered column for hero and text sections.

---

## 7. Border Radius

All radii are consistent across elements. The system uses exactly two radius
families: a uniform 9px for contained shapes, and a full-pill for stadium shapes.

### Named Radii

| Element | Value | CSS Token |
|---|---|---|
| Cards | 9px | `--radius-cards` |
| Buttons | 9px | `--radius-buttons` |
| Badges | 9px | `--radius-badges` |
| Inputs | 9px | `--radius-inputs` |
| Pills (tab switchers, tags) | 9999px | `--radius-pills` |

### Generic Radius Tokens

These exist in the token system for component-agnostic use:

| Token | Value | CSS Token |
|---|---|---|
| lg | 8.96px | `--radius-lg` |
| 2xl | 20px | `--radius-2xl` |
| full | 1600px | `--radius-full` |

**Note on radius-full vs radius-pills:** `--radius-full` (1600px) and
`--radius-pills` (9999px) are functionally equivalent for all elements smaller
than 3198px wide. Use `--radius-pills` for semantic intent (pill-shaped tabs,
case study tags), and `--radius-full` as a raw token when needed without
semantic connotation.

**Rule:** 9px on everything contained. 9999px exclusively for stadium-shaped tabs and tags. Do not introduce intermediate radii.

---

## 8. Shadows

The system contains exactly one shadow token. It is applied conservatively.

| Name | Value | CSS Token | Application |
|---|---|---|---|
| md | `rgba(39, 36, 33, 0.1) 0px 4px 12px 0px` | `--shadow-md` | Elevated feature cards only |

**Rules:**
- Do not apply `--shadow-md` to buttons, inputs, navigation, modals, tooltips, or any inline component
- Do not stack multiple shadows on any element
- Do not create additional shadow tokens with higher opacity or larger spread
- The shadow uses the Ink color (`#272421` = rgb 39, 36, 33) at 10% opacity, maintaining the warm monochrome cast even in elevation

---

## 9. Imagery and Illustration

Imagery is the only source of chromatic color in the entire system. It appears
in exactly one context: content cards (use case cards, experiment cards, result
cards in the Mosaic simulation interface).

### Gradient Artwork

- **Style:** Abstract, organic, high-chroma gradient compositions
- **Color palette:** Complementary and split-complementary harmonies (violet-to-orange, teal-to-red, indigo-to-amber)
- **Texture:** Subtle grain overlay giving a pigment-mixing-on-wet-paper quality
- **Crop:** Full-bleed within the card area; 9px radius on the card clips the image
- **No text inside the gradient field.** Labels always sit at the bottom-left corner with 16–24px inset, either directly on the image's naturally darker edge, or on a minimal white overlay strip

### Icon Illustrations

Icons inside platform feature cards are simple geometric line-and-fill
constructions: hexagons, circles, connecting dots — rendered in Ink on the warm
card surface. No chromatic icon fills. No product screenshots. No people photography.

### For Mosaic Specifically

The simulation-related content cards (topology comparison cards, experiment result
cards) use the same gradient treatment. The simulation network graph rendered by
D3.js is the only interactive visual — it inherits the Ink color system for edges
and uses the single shadow for the canvas element's elevation.

---

## 10. Components

### Primary Action Button

**Usage:** The only filled button style in the system.

| Property | Value |
|---|---|
| Background | `#272421` (Ink) |
| Text color | `#ffffff` (White) |
| Font | 13px Diatype Mono, uppercase |
| Letter spacing | 0.090em |
| Font weight | 400 |
| Border radius | 9px |
| Padding | 10px 24px |
| Border | none |
| Optional | Trailing arrow icon for directional actions |

Usage examples: navigation CONTACT button, hero BOOK A DEMO button, simulation RUN button.

### Secondary / Ghost Button

**Usage:** Secondary action alongside a primary button, or when a neutral choice is needed.

| Property | Value |
|---|---|
| Background | transparent |
| Text color | `#272421` (Ink) |
| Font | 13px Diatype Mono, uppercase |
| Letter spacing | 0.090em |
| Border | 1px solid `#edebe8` (Paper Warm) |
| Border radius | 9px |
| Padding | 10px 24px |

### Workflow / Segmented Tab Pill

**Usage:** Switching between platform stages or simulation modes.

| State | Background | Text | Border |
|---|---|---|---|
| Active | `#272421` (Ink) | `#ffffff` (White) | none |
| Inactive | transparent | `#272421` (Ink) | 1px solid `#272421` |

- Border radius: 9999px (stadium)
- Font: 13px Diatype Mono, uppercase, 0.090em tracking
- Padding: 10px 20px
- Gap between pills: 4–8px

### Use Case Card / Content Card

**Usage:** Primary content card showing a simulation experiment, use case, or result.

| Property | Value |
|---|---|
| Image | Full-bleed abstract gradient composition |
| Border radius | 9px |
| Border | none |
| Shadow | none (image provides visual energy) |
| Label | White 15px Diatype 500, bottom-left, 16–24px inset |
| Grid | 3-column desktop, gap 12–16px |

### Feature / Platform Card

**Usage:** Descriptive card for a platform capability or simulation module.

| Property | Value |
|---|---|
| Background | `#edebe8` (Paper Warm / Soft Surface) |
| Border radius | 9px |
| Shadow | `rgba(39, 36, 33, 0.1) 0px 4px 12px 0px` |
| Padding | 24–32px |
| Internal layout | Two-column: left 160x160 icon area, right text block |
| Step label | 11px Diatype Mono uppercase, Stone (`#7d7c7a`) |
| Heading | 24–32px Egyptienne F LT, Ink |
| Body | 15px Diatype 400, Ink |
| Grid | 2-column desktop |

### Step Number Label

**Usage:** Micro-label identifying a numbered section (e.g., "001 TOPOLOGY", "002 PRESTIGE").

| Property | Value |
|---|---|
| Font | 11px Diatype Mono |
| Case | UPPERCASE |
| Letter spacing | 0.090em |
| Color | Stone (`#7d7c7a`) |
| Tracking | Wide |

Always positioned above a heading. Acts as typographic furniture, not navigation.

### Case Study Tag / Pill Tag

**Usage:** Labeling a logo or result as a specific category.

| Property | Value |
|---|---|
| Background | `#edebe8` (Paper Warm) |
| Text | `#272421` (Ink) |
| Font | 11px Diatype Mono, uppercase |
| Letter spacing | 0.090em |
| Border radius | 9999px (pill) |
| Padding | 6px 12px |

### Customer / Institution Logo Strip

**Usage:** Social proof or data source attribution band.

- Single row, centered within 1200px max-width
- Logos rendered in Stone (`#7d7c7a`) grayscale, each roughly 100–140px wide
- Separated by 80–120px of whitespace
- No borders, no backgrounds — logos float on White canvas
- Optional Case Study / Source tag (Paper Warm background, Ink text, pill shape) beneath a selected logo

---

## 11. Navigation

### Primary Navigation Bar

| Property | Value |
|---|---|
| Background | `#ffffff` (White) |
| Bottom border | 1px solid `#edebe8` (optional — borderless is acceptable) |
| Height | 72–80px |
| Horizontal padding | 24px inside 1200px max-width container |
| Logo position | Left |
| Nav items | Centered, uppercase Diatype Mono 13px, 0.090em tracking, Ink |
| Primary CTA | Right-aligned, filled dark button (CONTACT / RUN) |
| Sticky behavior | Not specified — treat as non-sticky unless scroll behavior is explicitly added |
| Sidebar / mega-menu | Not in system — do not introduce |

### Logo Mark

Three-dot cluster icon (representing network nodes or a constellation) paired with
"Mosaic" in Diatype 500 Ink. No chromatic fills on the mark.

---

## 12. Forms

### Text Input

| Property | Value |
|---|---|
| Border | 1px solid `#edebe8` (Paper Warm) |
| Border radius | 9px |
| Background | `#ffffff` (White) |
| Text | 15px Diatype 400, Ink |
| Placeholder | 15px Diatype 400, Stone |
| Focus border | 1px solid `#272421` (Ink) |
| Shadow on focus | none |

### Parameter Sliders (Mosaic-specific)

Simulation parameter controls in the ControlPanel component follow the same
monochrome discipline:
- Track: Paper Warm (`#edebe8`)
- Filled track / thumb: Ink (`#272421`)
- Value label: 13px Diatype Mono, Stone
- No chromatic fill on any range state

### Labels

All form field labels use 11px Diatype Mono, uppercase, 0.090em tracking, Stone.
This is the same pattern as step number labels and nav items — consistent typographic
furniture throughout the system.

---

## 13. Charts and Data Visualization

This section applies specifically to Mosaic's simulation output visualizations:
the D3.js network graph, Recharts time series, and UMAP scatter plot.

### D3.js Network Graph

- **Node default fill:** Paper Warm (`#edebe8`)
- **Node stroke:** Ink (`#272421`), 1px
- **Node size:** 3px + centrality * 12px (hub agents visually larger)
- **Node cluster coloring:** Use a limited monochrome-adjacent palette for cluster
  differentiation. Acceptable: shades derived from the system neutrals, or use
  the gradient artwork palette (the abstract gradient colors) applied to node fills
  as the *only* acceptable chromatic element in the visualization layer. This is
  analogous to the gradient artwork rule on content cards.
- **Edge stroke:** Stone (`#7d7c7a`), 0.5px opacity 0.6
- **Edge hover:** Ink stroke, opacity 1.0
- **Canvas background:** White (`#ffffff`)
- **Shadow on canvas container:** `--shadow-md`
- **Tooltip:** Paper Warm background, Ink text, 9px radius, 12px Diatype body

### Recharts Time Series

- **Line colors:** Use Ink for primary series; Stone for secondary series
- **Grid lines:** Paper Warm (`#edebe8`), 1px
- **Axis labels:** 11px Diatype Mono, Stone, uppercase
- **Legend labels:** 11px Diatype Mono, Ink, uppercase
- **Tooltip:** Paper Warm background, Ink text, 9px radius

### UMAP Scatter Plot

- **Point fill:** Follow the same cluster coloring convention as the network graph
- **Point size:** 4px default
- **Background:** White
- **Timestep slider:** Matches the form slider specification above

### General Visualization Rules

- No chromatic axis fills or panel backgrounds
- All annotation text uses Diatype Mono, uppercase, Stone
- Figure titles use Diatype 500, Ink, heading-sm size (24px)
- Never use red/green for convergence success/failure — use Ink/Stone with an icon

---

## 14. Interaction States

The system defines states through border changes, background tints, and cursor
changes — never through chromatic color introduction.

| State | Treatment |
|---|---|
| Default | As specified per component |
| Hover (button) | Slight opacity reduction on Ink fill (0.85–0.90); or Paper Warm background darkens to Paper Cool for ghost buttons |
| Hover (card) | Cursor pointer; optional subtle lift (reduce shadow opacity by half) |
| Hover (nav item) | Ink text, underline 1px Ink |
| Focus | 1px border becomes 2px Ink on inputs; outline: 2px solid `#272421` offset 2px for keyboard navigation |
| Active / Pressed | Ink fill button: scale(0.98); Ghost button: Paper Warm background |
| Disabled | Stone text, Paper Cool background, cursor not-allowed |
| Loading | Spinner in Ink, no background color change on the button |

**Loading state for Run button (Mosaic-specific):**
While the simulation is running, the primary button should enter a disabled-like
state with a minimal Ink-colored spinner icon appended. Button text changes to
a status string (e.g., "RUNNING…") in the same Diatype Mono uppercase style.

---

## 15. Responsive Design

The design specification primarily targets desktop (>= 1200px). Breakpoints are
not formally specified in the source material, but the following rules apply:

| Breakpoint | Behavior |
|---|---|
| >= 1200px | Full layout: 1200px max-width container, 3-column card grid, 2-column feature grid |
| 768px – 1199px | Reduce card grid to 2 columns; reduce feature grid to 1 column; maintain all spacing tokens |
| < 768px | Single column layout; reduce display type sizes by one scale step; maintain 24px side padding |

The simulation control panel (React frontend) is intended for desktop use.
Mobile optimization is out of scope for Phase 3 but the layout should not break
at tablet widths.

---

## 16. Accessibility

**Contrast ratios:**
- Ink (`#272421`) on White (`#ffffff`): approximately 15.5:1 — exceeds WCAG AAA
- Stone (`#7d7c7a`) on White (`#ffffff`): approximately 4.6:1 — meets WCAG AA for normal text
- White (`#ffffff`) on Ink (`#272421`) fills: approximately 15.5:1 — exceeds WCAG AAA

**Color-only communication:** The system explicitly avoids using color alone to
convey status (no success green, no error red). All status states use icons plus
text. This is compliant with WCAG 1.4.1 (Use of Color).

**Focus indicators:** All interactive elements require a visible focus ring.
Use `outline: 2px solid #272421; outline-offset: 2px` as the universal focus style.

**Font sizes:** The minimum size in the system is 11px (Diatype Mono, captions
only). Body text at 15px comfortably meets legibility standards. Do not reduce
body text below 14px.

**Keyboard navigation:** All interactive controls (simulation run, topology
selector, parameter sliders) must be keyboard-accessible. The D3.js network
graph should support keyboard navigation for node selection if feasible in Phase 3.

---

## 17. Design Tokens Reference

This section documents all tokens from `tokens.json` in a human-readable format.
These are the canonical values that CSS properties should reference.

### Color Tokens

| Token Key | Value | Description |
|---|---|---|
| `color.ink` | `#272421` | Primary text and dark fills |
| `color.paper-warm` | `#edebe8` | Borders, card surfaces |
| `color.paper-cool` | `#e3e3e2` | Inset wells, recessed surfaces |
| `color.mist` | `#eeeeed` | Subtle dividers, hover wash |
| `color.stone` | `#7d7c7a` | Secondary text, metadata |
| `color.charcoal` | `#333333` | In-content links |
| `color.white` | `#ffffff` | Canvas, inverse text |

### Surface Tokens

| Token Key | Value | Level | Description |
|---|---|---|---|
| `surface.canvas` | `#ffffff` | 1 | Page background |
| `surface.soft-surface` | `#edebe8` | 2 | Cards, panels |
| `surface.cool-surface` | `#e3e3e2` | 3 | Inset, recessed |
| `surface.inverse-surface` | `#272421` | 4 | Dark fills |

### Shadow Tokens

| Token Key | Value | Description |
|---|---|---|
| `shadow.md` | `rgba(39, 36, 33, 0.1) 0px 4px 12px 0px` | Single elevation shadow |

### Radius Tokens

| Token Key | Value | Description |
|---|---|---|
| `radius.lg` | `8.96px` | Standard component radius (~9px) |
| `radius.2xl` | `20px` | Large radius (reserved) |
| `radius.full` | `1600px` | Full-pill radius |

### Spacing Tokens

| Token Key | Value |
|---|---|
| `spacing.unit` | `4px` |
| `spacing.4` | `4px` |
| `spacing.8` | `8px` |
| `spacing.12` | `12px` |
| `spacing.16` | `16px` |
| `spacing.20` | `20px` |
| `spacing.24` | `24px` |
| `spacing.32` | `32px` |
| `spacing.48` | `48px` |
| `spacing.56` | `56px` |
| `spacing.60` | `60px` |
| `spacing.64` | `64px` |
| `spacing.76` | `76px` |
| `spacing.80` | `80px` |
| `spacing.84` | `84px` |
| `spacing.88` | `88px` |
| `spacing.136` | `136px` |

---

## 18. CSS Custom Properties

The complete set of custom properties to be declared in `:root`. This combines
`variables.css` (which includes all layout and named-radius tokens) with the
font weight tokens that `theme.css` omits. `variables.css` is the more complete
of the two CSS files and is the authoritative implementation reference.

```css
:root {
  /* ── Colors ─────────────────────────────────────────────────────── */
  --color-ink:        #272421;
  --color-paper-warm: #edebe8;
  --color-paper-cool: #e3e3e2;
  --color-mist:       #eeeeed;
  --color-stone:      #7d7c7a;
  --color-charcoal:   #333333;
  --color-white:      #ffffff;

  /* ── Surfaces ────────────────────────────────────────────────────── */
  --surface-canvas:          #ffffff;
  --surface-soft-surface:    #edebe8;
  --surface-cool-surface:    #e3e3e2;
  --surface-inverse-surface: #272421;

  /* ── Typography — Font Families ──────────────────────────────────── */
  --font-egyptienne-f-lt: 'Egyptienne F LT', ui-sans-serif, system-ui,
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-diatype: 'Diatype', ui-sans-serif, system-ui,
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-diatype-mono: 'Diatype Mono', ui-monospace, SFMono-Regular,
    Menlo, Monaco, Consolas, monospace;

  /* ── Typography — Weights ────────────────────────────────────────── */
  --font-weight-regular: 400;
  --font-weight-medium:  500;
  --font-weight-bold:    700;

  /* ── Typography — Scale ──────────────────────────────────────────── */
  --text-caption:          11px;
  --leading-caption:       1.4;
  --tracking-caption:      0.33px;

  --text-body:             15px;
  --leading-body:          1.43;
  --tracking-body:         0.27px;

  --text-subheading:       18px;
  --leading-subheading:    1.3;
  --tracking-subheading:   0.32px;

  --text-heading-sm:       24px;
  --leading-heading-sm:    1.3;
  --tracking-heading-sm:   0.43px;

  --text-heading:          32px;
  --leading-heading:       1.2;
  --tracking-heading:      -0.96px;

  --text-heading-lg:       48px;
  --leading-heading-lg:    1.2;
  --tracking-heading-lg:   -1.44px;

  --text-display:          77px;
  --leading-display:       1;
  --tracking-display:      -2.16px;

  --text-display-xl:       94px;
  --leading-display-xl:    0.9;
  --tracking-display-xl:   -2.82px;

  /* ── Spacing ─────────────────────────────────────────────────────── */
  --spacing-unit: 4px;
  --spacing-4:    4px;
  --spacing-8:    8px;
  --spacing-12:   12px;
  --spacing-16:   16px;
  --spacing-20:   20px;
  --spacing-24:   24px;
  --spacing-32:   32px;
  --spacing-48:   48px;
  --spacing-56:   56px;
  --spacing-60:   60px;
  --spacing-64:   64px;
  --spacing-76:   76px;
  --spacing-80:   80px;
  --spacing-84:   84px;
  --spacing-88:   88px;
  --spacing-136:  136px;

  /* ── Layout ──────────────────────────────────────────────────────── */
  --page-max-width: 1200px;
  --section-gap:    96px;
  --card-padding:   24px;
  --element-gap:    8px;

  /* ── Border Radius ───────────────────────────────────────────────── */
  --radius-lg:      8.96px;
  --radius-2xl:     20px;
  --radius-full:    1600px;

  /* Named radii — prefer these over generic tokens */
  --radius-cards:   9px;
  --radius-buttons: 9px;
  --radius-badges:  9px;
  --radius-inputs:  9px;
  --radius-pills:   9999px;

  /* ── Shadows ─────────────────────────────────────────────────────── */
  --shadow-md: rgba(39, 36, 33, 0.1) 0px 4px 12px 0px;
}
```

### Differences Between theme.css and variables.css

`theme.css` uses the `@theme` block (Tailwind v4 syntax). `variables.css` uses
the standard `:root` block (vanilla CSS and all frameworks). The property values
are identical. `variables.css` is more complete: it additionally includes
`--font-weight-*` tokens, `--spacing-unit`, layout tokens (`--page-max-width`,
`--section-gap`, `--card-padding`, `--element-gap`), named radius tokens
(`--radius-cards`, `--radius-buttons`, `--radius-badges`, `--radius-inputs`,
`--radius-pills`), and surface alias tokens (`--surface-*`). Use `variables.css`
as the implementation base.

---

## 19. Frontend Conventions

### React Component Conventions (Phase 3)

- All colors, spacing, and type sizes are consumed via CSS custom properties —
  never hardcoded hex values in component styles
- Component-level styles use CSS Modules or a single `index.css` importing
  variables from `:root`
- No Tailwind unless explicitly decided — the existing source material includes
  a Tailwind v4 `@theme` block (`theme.css`), but the project uses vanilla CSS
  per `architecture.md`

### Naming Convention

Component file names use PascalCase (`NetworkGraph.jsx`). CSS class names use
kebab-case (`network-graph`, `control-panel`). Token variable names follow the
established `--category-name` pattern already defined in variables.css.

### D3.js Integration

The D3.js network graph is a React component that mounts D3 into a ref'd SVG
element. Simulation data (nodes, edges, centrality, cluster ids) is received as
props from the API response. D3 handles render; React handles data flow. No
D3 state management outside the SVG ref.

### No Dark Mode

The system is light-only. There is no dark theme token set, no `prefers-color-scheme`
media query, and no theme toggle. Do not add dark mode support without explicit
design specification.

---

## 20. Do's and Don'ts

### Do

- Use Egyptienne F LT (or Source Serif Pro) at 77–94px, weight 400, line-height 0.9, -0.030em tracking for all hero and section headlines. Never set the serif above 100px or below 18px.
- Use 13px Diatype Mono uppercase with 0.090em tracking for every nav item, button label, and step label.
- Fill all primary action buttons with Ink (`#272421`), White text, 9px radius, and 10px 24px padding.
- Apply 9px border-radius to every card, button, badge, and input. Use 9999px only for stadium-shaped pills and tags.
- Apply `--shadow-md` only to elevated feature cards. Nowhere else.
- Use Paper Warm (`#edebe8`) as the card/panel surface and White as the canvas. Use Paper Cool only for inset wells.
- Render gradient artwork only on content cards. Treat it as the only source of chromatic color in the interface.
- Communicate status with icons and text — not color.
- Declare all spacing, color, and type values through CSS custom properties defined in `:root`.

### Don't

- Do not introduce any chromatic brand color, accent, or CTA fill. The primary action is a dark neutral fill.
- Do not use Egyptienne F for body copy, button labels, or any UI chrome.
- Do not use pure `#000000` — always use Ink `#272421`.
- Do not use font-weight 700 on body text or headlines. Reserve bold for rare emphasis.
- Do not apply shadows to buttons, inputs, modals, or tooltips. Only elevated cards.
- Do not use letter-spacing wider than 0.090em or tighter than -0.030em.
- Do not place text inside the gradient artwork field on content cards.
- Do not add a dark mode.
- Do not hardcode color values in component styles — always reference a CSS custom property.
- Do not deviate from 9px radius for contained shapes or 9999px for pill shapes.

---

*Last updated: 2026-07-09*  
*Source files: `DESIGN (2).md`, `theme.css`, `variables.css`, `tokens.json`*
