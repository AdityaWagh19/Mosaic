# Mosaic — Design Specification

**Version:** 2.0
**Theme:** Light only
**Source material:** `DESIGN (3).md`, `tokens (1).json`, `variables (1).css`, `theme (1).css`
**Last updated:** 2026-07-11

This is the single source of truth for Mosaic’s visual system. It supersedes the previous warm editorial specification. The source files are retained for traceability; implementers should use this document and its canonical token names.

---

## 1. Design philosophy

**Floating pill in a white void — one blue spark on infinite paper.**

Mosaic is deliberately sparse and tool-like: a laboratory-clean white canvas, black typography, gray hairlines, and a single electric Signal Blue accent. The primary chrome is a centered floating pill navigation. Components are flat and precise; borders and whisper-thin shadows, not layered elevation, establish structure.

Inter Variable is the sole typeface. Its tight global tracking gives even compact UI text an engineered quality. A 62px display size is reserved for occasional hero statements; nearly all other text is 16px or smaller.

### Principles

- **One saturated interface color.** Signal Blue is for the primary CTA, active navigation, and logo icon. All other chrome is monochrome.
- **Density with room to breathe.** The scale is compact inside components, while page sections use generous 128px separation.
- **Structure over decoration.** White surfaces, 1px hairlines, and black text do the visual work. Do not introduce gradients, tinted panels, or colored elevations.
- **Colorful data is content.** The illustration-only palette may be used in charts and explanatory graphics when it improves comprehension, never as general UI chrome.
- **One voice.** Use Inter Variable throughout: headings, body, controls, navigation, labels, and chart annotation.

---

## 2. Color system

| Name | Value | Token | Role |
|---|---:|---|---|
| Signal Blue | `#0077ff` | `--color-signal-blue` | Primary CTA fill, active navigation, logo icon; the only saturated chrome color. |
| Paper | `#ffffff` | `--color-paper` | Page canvas, cards, inputs, pill navigation, and text on blue actions. |
| Ink | `#000000` | `--color-ink` | Primary text, icon strokes, hairline structural accents, logo mark. |
| Hairline | `#e5e7eb` | `--color-hairline` | Borders, dividers, card edges, inputs, and image frames. |
| Smoke | `#b8b8b8` | `--color-smoke` | Shadow tint and secondary border accent. |
| Graphite | `#525252` | `--color-graphite` | Secondary body text, muted links, list items. |
| Ash | `#737373` | `--color-ash` | Tertiary text, resting icons, placeholders, secondary labels. |
| Mercury | `#a3a3a3` | `--color-mercury` | Decorative strokes and disabled icon state. |
| Slate | `#ababab` | `--color-slate` | Quiet borders and nearly invisible dense-layout dividers. |
| Ember | `#f97316` | `--color-ember` | Illustration and visualization accent only. |
| Amber | `#f59e0b` | `--color-amber` | Illustration and visualization accent only. |
| Crimson | `#ef4444` | `--color-crimson` | Short emphasized text, tags, and graphics only; never generic chrome. |
| Deep Signal | `#2563eb` | `--color-deep-signal` | Illustration and icon-set accent only; not an interface color. |

### Color rules

- Use Ink for primary text; Graphite for secondary text; Ash for tertiary text and placeholders.
- Use Paper for the page and almost every surface. White-on-white surfaces are separated by Hairline borders or the subtle shadow.
- Signal Blue is the only filled primary action color. Do not use it for ordinary links, borders, or decorative backgrounds.
- Ember, Amber, Crimson, and Deep Signal are quarantined to illustrations and data graphics. Never use them for navigation, buttons, form states, or page backgrounds.
- Do not rely on color alone for status. Pair an icon and clear text with any state.

---

## 3. Typography

### Typeface

Use `InterVariable` exclusively. If unavailable, use Inter Variable, then the system sans-serif fallback.

```css
--font-intervariable: 'InterVariable', ui-sans-serif, system-ui, -apple-system,
  BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

- **Weights:** 400, 500, 600, 700
- **Global letter spacing:** `-0.025em`
- **Display type:** 62px, weight 500. Use no more than once in a page section.

### Type scale

| Role | Size | Weight | Line height | Letter spacing | Token |
|---|---:|---:|---:|---:|---|
| micro | 10px | 700 | 1.4 | -0.25px | `--text-micro` |
| caption | 12px | 400 | 1.5 | -0.3px | `--text-caption` |
| body-sm | 14px | 400 | 1.43 | -0.35px | `--text-body-sm` |
| body-lg | 16px | 400 | 1.5 | -0.4px | `--text-body-lg` |
| display | 62px | 500 | 1.16 | -1.55px | `--text-display` |

Use 12px/500 for compact navigation and button labels, 14px for controls and concise supporting content, and 16px for normal reading text. Use 600 or 700 only where hierarchy requires it.

---

## 4. Spacing, layout, and shape

### Spacing

The base unit is **4px**. Component density is compact.

| Value | Token |
|---:|---|
| 4px | `--spacing-4` |
| 8px | `--spacing-8` |
| 12px | `--spacing-12` |
| 16px | `--spacing-16` |
| 24px | `--spacing-24` |
| 32px | `--spacing-32` |
| 48px | `--spacing-48` |
| 96px | `--spacing-96` |
| 128px | `--spacing-128` |
| 180px | `--spacing-180` |

### Layout

| Property | Value | Token |
|---|---:|---|
| Page max width | 1200px | `--page-max-width` |
| Section gap | 128px | `--section-gap` |
| Card padding | 16px | `--card-padding` |
| Element gap | 8px | `--element-gap` |

- Center content within a 1200px maximum-width container.
- Keep 24px horizontal gutters at tablet and desktop widths; use at least 16px on small screens.
- Favor centered stacks, two-column text-and-image blocks, and three-column feature grids on desktop.
- Separate major sections with 128px whitespace and/or a flush Hairline divider.

### Radius

| Element | Value | Token |
|---|---:|---|
| Buttons and inputs | 8px | `--radius-buttons`, `--radius-inputs` |
| Cards and images | 16px | `--radius-cards`, `--radius-images` |
| Floating navigation, tags, capsules | 9999px | `--radius-pills`, `--radius-nav-pill` |

The raw radius scale is 8px (`lg`), 12px (`xl`), 16px (`2xl`), 24px (`3xl`), and full (`9999px`). Do not mix radius scales within a component family.

---

## 5. Surfaces and elevation

| Level | Name | Value | Purpose |
|---:|---|---:|---|
| 0 | Paper | `#ffffff` | Page canvas. |
| 1 | Card | `#ffffff` | Content containers and navigation pill, distinguished by a Hairline border or subtle shadow. |
| 2 | Action | `#0077ff` | Primary CTA fill; the only chromatic elevated surface. |

| Shadow | Value | Token | Use |
|---|---|---|---|
| subtle | `rgba(0, 0, 0, 0.25) 0 0 1px 0` | `--shadow-subtle` | Pill navigation, CTA buttons, and optionally content cards. |
| xl | `rgba(0, 0, 0, 0.25) 0 25px 50px -12px` | `--shadow-xl` | Rare elevated feature cards only. |

Never add gradients, colored shadows, or elevation stacks. A card is normally defined by its Hairline border, not a shadow.

---

## 6. Components

### Floating pill navigation

The signature site chrome: a Paper pill centered horizontally, approximately 16px from the top. Use a full radius and `--shadow-subtle`. It contains an Ink logo wordmark, Graphite 12px/500 text links, and a Signal Blue sign-up or primary-action button.

- Logo icon: approximately 20px square, Signal Blue.
- Wordmark: 12px, 700, Ink.
- Links: 12px, 500, Graphite; text-only with about 12px horizontal padding.
- CTA: Signal Blue fill, Paper text, 8px radius, 6px 12px padding, 12px/500 type.
- The navigation reads as one floating object, not a fixed full-width header.

### Primary CTA button

- Signal Blue fill; Paper text; 8px radius; 6px 12px padding.
- Inter Variable, 12px, 500; optional 12px trailing arrow.
- Apply `--shadow-subtle`.
- Do not use a different colored hover fill. A small opacity, brightness, or shadow adjustment is sufficient.

### Secondary action and inline link

Secondary navigation is text-only: Graphite, Inter Variable 12–14px, weight 500, no filled background. Inline links are Graphite—not blue—and are distinguished through weight and optional underline, not chromatic emphasis.

### Content card

- Paper surface; 16px radius; 16px padding.
- 1px Hairline border; no shadow or only `--shadow-subtle`.
- Use for grouped information, simulation results, configuration areas, and explanatory content.

### Elevated feature card

Paper surface with a 16px radius and `--shadow-xl`. Reserve for a hero-adjacent insight or one or two key feature highlights per page. Do not use in grids by default.

### Text input

- Paper fill; 1px Hairline border; 8px radius; 8px vertical and 12px horizontal padding.
- 14px/400 Ink input text; Ash placeholder text.
- On keyboard focus, use a clearly visible Ink outline or border. Do not substitute a blue glow for an accessible focus indicator.

### Dividers, images, icons, and lists

- **Divider:** 1px Hairline, full container width, flush between content blocks.
- **Framed image:** 16px radius and 1px Hairline border.
- **Icons:** 1.5px strokes. Use Ink for primary UI, Ash for secondary UI, Paper on Signal Blue. Decorative icons may use the illustration palette.
- **Lists:** Graphite 12px text and 8px row spacing.

---

## 7. Mosaic product and data visualization guidance

Mosaic’s network graph, time-series charts, scatter plots, and simulation controls follow the same chrome rules while allowing restrained semantic color inside the visualization itself.

### Simulation controls

- Place controls in Paper cards with Hairline borders and 16px padding.
- Inputs, selects, and sliders use Ink text, Hairline tracks/borders, Ash secondary labels, and 8px control radii.
- The Run action is the primary Signal Blue CTA. Loading and disabled states must retain a text label plus icon/spinner; do not signal state only with color.
- Use 12px or 14px labels, not uppercase mono labels from the retired design system.

### Network graph and charts

- Canvas and plot background: Paper; chart container: Paper with Hairline border and 16px radius.
- Primary lines, nodes, axes, and annotation: Ink. Supporting series and grid lines: Graphite, Ash, or Hairline as appropriate.
- Use Signal Blue only for the selected or primary series. Do not make every series blue.
- When cluster differentiation is necessary, use Ember, Amber, Crimson, and Deep Signal only within the visualization. Pair color with labels, shapes, hover details, or patterns for accessibility.
- Tooltips: Paper background, Ink text, Hairline border, 8px radius, `--shadow-subtle`.
- Use Inter Variable for all axes, legends, and annotation. Keep labels at 12px or above whenever space permits.

---

## 8. Interaction, responsive design, and accessibility

### Interaction states

| State | Treatment |
|---|---|
| Hover | Preserve the component’s color role; use a subtle opacity, border, or shadow change. |
| Focus | Visible 2px Ink outline with 2px offset, or an equivalent clearly visible Ink border. |
| Active | Small `scale(0.98)` press treatment is permitted for buttons. |
| Disabled | Ash or Mercury label/icon, restrained Paper/Hairline treatment, and `not-allowed` cursor. |
| Loading | Retain the action label and add a progress indicator; do not replace it with color alone. |

### Responsive behavior

| Width | Behavior |
|---|---|
| ≥1200px | 1200px container; three-column feature grid and two-column media/text blocks. |
| 768–1199px | Two-column feature grid; maintain 16–24px outer gutters. |
| <768px | Single-column content; simplify or scroll the pill navigation as needed; keep controls comfortably tappable. |

Reduce the 62px display type on smaller screens as needed, but preserve its distinct role. Do not reduce regular body text below 14px.

### Accessibility requirements

- Ink on Paper and Paper on Signal Blue supply strong contrast; verify any use of Graphite, Ash, or illustration colors at the actual text size.
- All controls must have keyboard access and a visible focus indicator.
- Never communicate simulation status, chart meaning, or validation errors with color alone.
- Use semantic labels and text alternatives for data visualizations; expose a tabular or textual summary where interaction alone would hide key results.
- Respect reduced-motion preferences for animated charts, transitions, and floating effects.

---

## 9. Canonical CSS tokens

Use custom properties rather than hard-coded values in component styles.

```css
:root {
  /* Colors */
  --color-signal-blue: #0077ff;
  --color-paper: #ffffff;
  --color-ink: #000000;
  --color-hairline: #e5e7eb;
  --color-smoke: #b8b8b8;
  --color-graphite: #525252;
  --color-ash: #737373;
  --color-mercury: #a3a3a3;
  --color-slate: #ababab;
  --color-ember: #f97316;
  --color-amber: #f59e0b;
  --color-crimson: #ef4444;
  --color-deep-signal: #2563eb;

  /* Typography */
  --font-intervariable: 'InterVariable', ui-sans-serif, system-ui, -apple-system,
    BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --text-micro: 10px;
  --leading-micro: 1.4;
  --tracking-micro: -0.25px;
  --text-caption: 12px;
  --leading-caption: 1.5;
  --tracking-caption: -0.3px;
  --text-body-sm: 14px;
  --leading-body-sm: 1.43;
  --tracking-body-sm: -0.35px;
  --text-body-lg: 16px;
  --leading-body-lg: 1.5;
  --tracking-body-lg: -0.4px;
  --text-display: 62px;
  --leading-display: 1.16;
  --tracking-display: -1.55px;

  /* Spacing and layout */
  --spacing-unit: 4px;
  --spacing-4: 4px;
  --spacing-8: 8px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-24: 24px;
  --spacing-32: 32px;
  --spacing-48: 48px;
  --spacing-96: 96px;
  --spacing-128: 128px;
  --spacing-180: 180px;
  --page-max-width: 1200px;
  --section-gap: 128px;
  --card-padding: 16px;
  --element-gap: 8px;

  /* Shape and elevation */
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-3xl: 24px;
  --radius-full: 9999px;
  --radius-cards: 16px;
  --radius-pills: 9999px;
  --radius-images: 16px;
  --radius-inputs: 8px;
  --radius-buttons: 8px;
  --radius-nav-pill: 9999px;
  --shadow-subtle: rgba(0, 0, 0, 0.25) 0 0 1px 0;
  --shadow-xl: rgba(0, 0, 0, 0.25) 0 25px 50px -12px;

  /* Surfaces */
  --surface-paper: #ffffff;
  --surface-card: #ffffff;
  --surface-action: #0077ff;
}
```

`theme (1).css` contains the Tailwind v4 `@theme` form of the same core tokens. `variables (1).css` is the complete vanilla-CSS implementation reference because it also contains layout, named-radius, surface, and font-weight variables.

---

## 10. Do and don’t

### Do

- Use Signal Blue only for the primary CTA, active navigation, and logo icon.
- Use Ink text and Hairline borders as the structural backbone of the interface.
- Apply 8px radii to interactive controls, 16px radii to cards and images, and full radii to capsules.
- Set Inter Variable text with tight `-0.025em` tracking.
- Keep standard component gaps at 8px and major section gaps at 128px.
- Reserve the dramatic extra-large shadow for a rare feature highlight.

### Don’t

- Do not continue using the previous warm-neutral palette, Egyptienne F, Diatype, or Diatype Mono tokens.
- Do not add gradients, tinted elevations, or colored shadows to UI chrome.
- Do not color ordinary links blue.
- Do not use illustration colors for buttons, navigation, inputs, or generic status states.
- Do not use display type repeatedly within one section.
- Do not add dark mode without a separate, explicit specification.
