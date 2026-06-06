---
name: TORDIT
description: AI-powered TOR compliance auditing for Thai government procurement
colors:
  chula-pink: "#C23680"
  chula-pink-deep: "#A22D6B"
  neutral-bg: "#F8F9FA"
  surface: "#FFFFFF"
  surface-panel: "#F1F3F5"
  ink: "#111827"
  ink-secondary: "#4B5563"
  ink-muted: "#9CA3AF"
  border: "#E5E7EB"
  border-strong: "#D1D5DB"
  violation-bg: "#FEF2F2"
  violation-border: "#FECACA"
  violation-fg: "#DC2626"
  suggestion-bg: "#FFFBEB"
  suggestion-border: "#FDE68A"
  suggestion-fg: "#B45309"
  success-fg: "#16A34A"
typography:
  heading:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
  mono:
    fontFamily: "Geist Mono, ui-monospace, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.chula-pink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.chula-pink-deep}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-disabled:
    backgroundColor: "{colors.neutral-bg}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.md}"
    padding: "6px 10px"
  finding-card-violation:
    backgroundColor: "{colors.violation-bg}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  finding-card-suggestion:
    backgroundColor: "{colors.suggestion-bg}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  input-select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
---

# Design System: TORDIT

## 1. Overview

**Creative North Star: "The Examiner's Desk"**

TORDIT is a professional instrument for people whose job is to catch mistakes before they create legal liability. The interface should feel like the desk of a senior procurement examiner: ordered, citation-ready, and confident without being formal. Every element has a reason to be there. Nothing decorates; everything informs. The tone is measured and unhurried — the tool is not alarmed by violations, it simply states them and tells you how to fix them.

The palette is cool-neutral with a single warm accent: Chula Pink (`#C23680`), the institutional color of Chulalongkorn University, which developed this system. That pink is used exactly once per viewport at rest — on the primary action button. Everything else is near-white, gray, and semantic. Severity colors (red, amber, green) are status signals and are never used decoratively. Density is comfortable: breathing room around findings, enough whitespace to reduce the pressure of a compliance report, but not so sparse that navigation feels slow.

Thai text is first-class throughout. Body copy is set at 14px with a minimum 1.6 line-height — the baseline for legible Thai script at reading size. No Latin-optimized choices are imported untested. The interface must work as well for a committee member reading a 15-finding report as it does for a first-time user uploading their first PDF.

This system explicitly rejects: Thai government portal aesthetics (cluttered tables, institutional blue header bars, dated table-driven layouts, `.go.th` visual grammar); the 2024–2026 AI SaaS aesthetic (cream or sand page backgrounds, hero metric cards, gradient text, identical icon-card grids); legal compliance tool aesthetics (heavy navy, gold accents, serif body type, LexisNexis-family formality); and consumer app aesthetics (playful rounded shapes, bright multi-color palettes, onboarding mascots). If the interface could be mistaken for any of these, it has failed.

**Key Characteristics:**
- Cool-neutral surfaces with one institutional pink primary; all other accent use is semantic (red, amber, green for finding severity)
- Geist Sans throughout — one family, weight-contrast hierarchy (400 / 500 / 600), no display/body pairing
- Findings grouped by TOR section with expandable citation detail; rule ID visible in collapsed state
- One shadow tier (card ambient only); panels and the header are flat and border-separated
- Thai text at 14px body minimum with 1.6+ line-height

## 2. Colors: The Examiner's Palette

One institutional pink. One semantic spectrum. One neutral ramp. Color earns every appearance.

### Primary
- **Chula Pink** (`#C23680`, canonical oklch(47% 0.21 345)): The primary action anchor, drawn from Chulalongkorn University's institutional palette. Appears on primary buttons, focus rings, and active/selected state indicators only. Its rarity is the point — when something is Chula Pink, it means "the action lives here."
- **Chula Pink Deep** (`#A22D6B`, oklch(39% 0.21 345)): Hover and pressed state for primary surfaces. Never appears at rest.

### Secondary

Not defined. This system has one accent. Secondary visual weight is delivered through typography and border, not a second hue. Introducing a second accent color would dissolve the signal value of Chula Pink.

### Neutral
- **Ink** (`#111827`): Headings, primary body text, high-emphasis labels. Near-black, not pure black — softened without fading.
- **Ink Secondary** (`#4B5563`): Secondary body text, UI labels, section headers in the findings panel.
- **Ink Muted** (`#9CA3AF`): Placeholder text, timestamps, disabled labels, metadata. Verify 4.5:1 against every background before use — this value fails on light warm surfaces.
- **Page Background** (`#F8F9FA`): Body background. Cool-tinted near-white — reads as a workspace, not a marketing page. Not cream, not sand, not warm. The tint goes toward cool blue, not warm yellow.
- **Surface** (`#FFFFFF`): Card interiors, form controls, modal backgrounds, the PDF embed area.
- **Surface Panel** (`#F1F3F5`): The findings panel right column on the results page. A perceptible but subtle step down from Surface to visually separate the review pane from the document pane.
- **Border** (`#E5E7EB`): Default dividers, card outlines, input strokes, the header bottom border.
- **Border Strong** (`#D1D5DB`): Drag-active drop zone border, stronger separators when Border is too subtle.

### Semantic (Finding Severity)
- **Violation Background** (`#FEF2F2`): Fill tint for "ผิดระเบียบ" (must-fix) finding cards.
- **Violation Border** (`#FECACA`): Border stroke for violation cards.
- **Violation Foreground** (`#DC2626`): Icon, badge text, and severity label for violations.
- **Suggestion Background** (`#FFFBEB`): Fill tint for "ควรปรับปรุง" (should-improve) cards.
- **Suggestion Border** (`#FDE68A`): Border stroke for suggestion cards.
- **Suggestion Foreground** (`#B45309`): Icon and severity label for suggestions.
- **Success Foreground** (`#16A34A`): "ตรวจสอบเสร็จแล้ว" status label, file-selected icon in the drop zone.

**The One Pink Rule.** Chula Pink appears on primary action buttons, focus rings, and the drag-active drop zone highlight — and nowhere else. It is not used on headings, decorative elements, borders, status text, or inactive states. If you reach for pink and it is not signaling a primary action or active selection, choose a different token.

**The Semantic Firewall Rule.** Red and amber are reserved exclusively for finding severity. Do not use violation-fg or suggestion-fg on any non-finding element — banners, tips, system warnings, or marketing copy. These colors carry audit meaning; diluting that meaning corrodes the report's credibility.

## 3. Typography

**Body + UI Font:** Geist (variable weight; `font-feature-settings: "cv11", "ss01"` recommended for Thai alternate glyph support)
**Mono Font:** Geist Mono (rule IDs, provision text, legal citation strings)

**Character:** One sans-serif family across every level of the hierarchy. No display/body pairing — this is a tool, not a publication. Weight contrast (400 body, 500 medium, 600 heading) plus size create the full hierarchy. Geist's geometric-humanist construction renders Thai characters well at small sizes, which is the primary typographic constraint here.

### Hierarchy
- **Heading** (600 weight, 1.25rem/20px, line-height 1.35, letter-spacing −0.01em): Page titles, the TORDIT wordmark. One per page.
- **Title** (500 weight, 0.875rem/14px, line-height 1.4): Filename in the header bar, findings panel section group labels (grouped by TOR topic), form section headers.
- **Body** (400 weight, 0.875rem/14px, line-height 1.6): Finding descriptions, suggested-fix text, citation prose, the loading message. The 1.6 line-height is the Thai-first baseline — do not compress it.
- **Label** (500 weight, 0.75rem/12px, line-height 1.4): Form field labels, severity badges (`ผิดระเบียบ` / `ควรปรับปรุง`), metadata, UI chips, status text in the header.
- **Mono** (400 weight, 0.75rem/12px, line-height 1.5): Rule IDs (`PENALTY-2`, `STRUCT-1`), raw provision text blocks, citation reference strings. Geist Mono at 12px renders these as data, distinct from prose.

**The Thai-First Rule.** Body and label prose must be set at 14px minimum — never 12px for running text. Thai script has tall ascenders and complex stacked characters; tighter line-heights clip them. A design that passes visual review against Latin placeholder copy can still fail when real Thai text is dropped in. Thai content is the real test. 12px (the `label` scale) is permitted only for genuinely short metadata strings (a timestamp, a rule code, a badge), never for sentences.

**The One Family Rule.** Geist only. No second sans, no serif for contrast, no display variant. If hierarchy feels flat, increase weight or reduce size — do not introduce a second typeface. Mixing font families in product UI reads as inconsistency, not richness.

## 4. Elevation

One shadow tier for floating content containers. Everything else is flat and border-separated.

Panels that tile edge-to-edge (the findings panel, the header bar, the PDF viewer area) carry no shadow. They are distinguished from each other by border strokes and background tint steps (Surface, Surface Panel, Page Background). Shadows are reserved for containers that genuinely float above the page background.

### Shadow Vocabulary
- **Card Ambient** (`box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)`): Applied to the upload card and any modal or floating container. Diffuse and low — signals "this surface is lifted" without competing visually with the finding cards inside it.

**The Flat-By-Default Rule.** Surfaces are flat at rest. The Card Ambient shadow is for one container type: a form or card that sits on the page background. If a component needs to signal elevation, try border + background tint before reaching for shadow. If that fails, the Card Ambient value is the only permitted answer.

**The One Tier Rule.** There is exactly one shadow value. No `shadow-lg`, no `shadow-heavy`, no colored glows, no drop shadows on text. If something needs more visual weight than the Card Ambient provides, achieve it through border stroke and background color.

## 5. Components

### Buttons

The primary button carries Chula Pink. All other states use shade or transparency, not new hues.

- **Shape:** Gently curved (8px radius, `rounded-md`)
- **Primary:** Chula Pink background (`#C23680`), white text. Padding 10px vertical, 16px horizontal. Label weight (500, 14px). Full-width on the upload card.
- **Primary Hover:** Chula Pink Deep (`#A22D6B`). Transition: `background-color 150ms ease-out`.
- **Primary Focus:** `outline: 2px solid #C23680; outline-offset: 2px;` The focus ring is the same Chula Pink — consistent with the color's action-signal role.
- **Disabled:** Page Background fill (`#F8F9FA`), Ink Muted text (`#9CA3AF`). `cursor: not-allowed`. Never a dimmed version of pink — token values, not opacity.
- **Ghost (Back/Secondary):** Transparent background, Ink Secondary text (`#4B5563`). Hover: Border-colored background tint. Used for the back arrow on the results page and secondary navigation actions.

### File Upload Dropzone

- **Default:** Page Background fill, dashed Border stroke (`#E5E7EB`, 2px). Upload icon in Ink Muted. Prompt text in Ink Secondary (14px/500) and Ink Muted (12px/400) for the constraints line.
- **Drag Active:** Dashed Chula Pink border, `rgba(194, 54, 128, 0.04)` fill. `transition: all 150ms ease-out`. The one place Chula Pink appears as a border.
- **File Selected:** Solid green border (`#86EFAC`), green fill (`#F0FDF4`), FileText icon in Success Foreground (`#16A34A`). Filename in Ink (500) and file size in Ink Muted (12px). A clear dismiss button (X) in the top-right corner of the zone.
- **Error State:** The drop zone itself does not show an error; errors surface in the form-level error message below it (red text on red-50 background, `rounded-lg`).

### Cards / Containers

- **Upload Card:** Surface white, Border stroke, Card Ambient shadow, 12px radius (`rounded-xl`). 24px padding. The only shadowed surface in the upload view.
- **Finding Card (Violation):** Violation Background fill, Violation Border stroke, 8px radius. No shadow. The border is full (all four sides) — no left-stripe accent.
- **Finding Card (Suggestion):** Suggestion Background fill, Suggestion Border stroke, 8px radius. No shadow. Same structure as violation, different palette.

### Inputs / Selects

- **Style:** Surface white, Border stroke (`#E5E7EB`), 8px radius. Padding 8px/12px. Body weight (400, 14px).
- **Focus:** Border shifts to Chula Pink (`#C23680`), `ring: 2px solid rgba(194, 54, 128, 0.25)`. No background change.
- **Disabled:** Page Background fill, Ink Muted text.

### Finding Card (Signature Component)

The central display primitive. Expandable, severity-coded, citation-anchored.

- **Collapsed:** Severity icon (AlertCircle for violation, AlertTriangle for suggestion) + severity badge + rule ID in Mono type + description in Body weight (clamped to 2 lines) + ChevronRight at trailing edge. The rule ID is visible here, collapsed — auditors need to scan IDs without opening each card.
- **Expanded:** A thin `border-t border-black/5` divides header from detail. Below: evidence blockquote (when present, with italic styling and "พบในเอกสาร ✓" verification indicator in Success Foreground), citation text with optional provision toggle ("ดูตัวบทกฎหมาย"), suggested fix in Body weight, error class number + Thai label.
- **Expand/collapse transition:** `max-height` or conditional render. 150ms ease-out. No opacity fade.

**The Citation-First Rule.** Rule ID and citation must both be accessible within one click from the collapsed state. Users are auditors cross-referencing against procurement law — they need to verify references rapidly, not hunt through expanded cards. The rule ID in mono type in the collapsed header is not optional.

### Header Bar

- **Height:** 48px
- **Background:** Surface white with Border bottom stroke (`#E5E7EB`)
- **Left:** Ghost back button (ArrowLeft icon + "กลับ" label hidden at small viewports)
- **Center:** Filename in Title weight (500, 14px), truncated. Status indicator (spinner + text, or status text) immediately after in Label weight.
- **No shadow.** The header is a border-separated flat surface.

### Status Indicators

- **Processing:** Loader2 spinner in Chula Pink (`#C23680`, `animate-spin`), "กำลังตรวจสอบ…" in Label weight, Chula Pink color.
- **Completed:** "ตรวจสอบเสร็จแล้ว" in Success Foreground (`#16A34A`), Label weight. No icon, no celebration.
- **Failed:** AlertCircle icon + error text in Violation Foreground (`#DC2626`).

## 6. Do's and Don'ts

### Do:
- **Do** use `#C23680` Chula Pink on exactly one type of element at a time: the primary button or the active focus ring. Its scarcity is its signal.
- **Do** set all Thai prose at 14px with `line-height: 1.6` minimum. Test the layout against real Thai content, not Latin placeholder text.
- **Do** show the rule ID (in Mono type) in the collapsed state of every finding card. Auditors scan by rule code; requiring a click to see it is a workflow failure.
- **Do** use full-border cards for finding severity (all four sides, matching tint background). Background fill + full border is the correct finding card pattern.
- **Do** apply the Card Ambient shadow only to the upload card and floating containers. The findings panel, header, and PDF viewer area are flat and border-separated.
- **Do** group findings by `topic_location` (the TOR section). The document's own structure is the navigation structure of the report.
- **Do** keep state transitions at 150ms ease-out. Users are in a compliance workflow; motion should be imperceptible, not choreographed.
- **Do** use `#F8F9FA` (cool-tinted near-white) for the page background. Never drift toward a warm tint.

### Don't:
- **Don't** use `border-left` with a colored accent on finding cards, list items, or any container. The side-stripe pattern is prohibited. Use full borders with background tint fills.
- **Don't** apply gradient text (`background-clip: text`) anywhere — rule IDs, headings, severity labels, or buttons are solid ink or solid Chula Pink.
- **Don't** reproduce Thai government portal aesthetics: no institutional blue header bars, no table-heavy grid layouts, no dated serif navigation type, no `.go.th` visual grammar.
- **Don't** use a cream, sand, warm-paper, or warm-tinted body background. The `#F8F9FA` page background is cool-neutral. Warming it drifts toward the AI SaaS template this system explicitly rejects.
- **Don't** use heavy navy, gold accents, or serif body type. The legal-compliance tool aesthetic directly conflicts with the "trusted-but-approachable" goal from PRODUCT.md.
- **Don't** use playful or consumer-app visual language: pill-shaped everything, multi-color accent palettes, emoji in status messages, animated mascots, or onboarding illustration.
- **Don't** use Chula Pink on more than one element type per viewport at rest. If two elements are pink simultaneously, one of them is wrong.
- **Don't** build identical icon-card grids for the findings list. Findings are structured audit data with variable content; they require an expandable detail pattern, not a promotional card layout.
- **Don't** introduce a second typeface — no display font for the TORDIT wordmark, no serif for citation text, no second sans for contrast. Geist at 600 weight is the heading. Geist Mono is the only permitted second face, and only for data strings (rule IDs, provisions).
- **Don't** disable a button by dimming it with `opacity: 0.5`. Disabled state uses explicit token values: `neutral-bg` fill, `ink-muted` text, `cursor: not-allowed`. Opacity dimming is invisible to users who rely on color contrast.
